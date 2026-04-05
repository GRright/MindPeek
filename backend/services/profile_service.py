"""
用户画像服务层
"""
import asyncio
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from ..models.database import UserModel, ProfileModel, ConversationModel, FeatureModel
from ..models.schemas import (
    FeatureCreate, FeatureResponse, MessageCreate, MessageResponse,
    ProfileResponse, ProfileSummary, UserProfileDetail
)
from ..agents.agent_engine import AgentOrchestrator
from ..knowledge_graph.hybrid_graph import knowledge_graph
from ..core.config import config_manager
from .memo_base_service import memo_base_service
from .feature_merger import feature_merger

DEFAULT_DECAY_CONFIG = {
    "enabled": True,
    "min_confidence": 0.3,
    "default_stability_period_days": 30,
    "default_decay_rate": 0.05
}


class ProfileService:
    """用户画像服务"""
    
    def __init__(self, db: AsyncSession, provider_type: str = None):
        self.db = db
        self.provider_type = provider_type or config_manager.get_default_provider()
        self.agent_orchestrator = AgentOrchestrator(self.provider_type)
    
    async def get_or_create_user(self, user_id: str, username: str = None) -> UserModel:
        """获取或创建用户"""
        result = await self.db.execute(
            select(UserModel).where(UserModel.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = UserModel(user_id=user_id, username=username)
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        
        return user
    
    async def add_conversation(self, user_id: str, message: MessageCreate) -> ConversationModel:
        """添加对话"""
        user = await self.get_or_create_user(user_id)

        conversation = ConversationModel(
            user_id=user_id,
            role=message.role.value,
            content=message.content,
            session_id=message.session_id
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        if memo_base_service.is_enabled():
            await memo_base_service.update_conversation(
                user_id, message.role.value, message.content, message.session_id
            )

        return conversation
    
    async def get_conversation_history(self, user_id: str, limit: int = 50) -> List[ConversationModel]:
        """获取对话历史"""
        result = await self.db.execute(
            select(ConversationModel)
            .where(ConversationModel.user_id == user_id)
            .order_by(desc(ConversationModel.timestamp))
            .limit(limit)
        )
        conversations = result.scalars().all()
        return list(reversed(conversations))
    
    async def add_feature(self, user_id: str, feature: FeatureCreate) -> FeatureModel:
        """添加特征（支持智能合并相似特征）"""
        user = await self.get_or_create_user(user_id)
        
        existing_result = await self.db.execute(
            select(FeatureModel).where(
                and_(
                    FeatureModel.user_id == user_id,
                    FeatureModel.feature_type == feature.feature_type,
                    FeatureModel.feature_value == feature.feature_value
                )
            )
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            if feature.confidence > existing.confidence:
                existing.confidence = feature.confidence
                existing.source_message = feature.source_message
                existing.reasoning = feature.reasoning
                existing.evidence = feature.evidence
            existing.verification_count = (existing.verification_count or 0) + 1
            existing.last_verified_at = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        
        all_features_result = await self.db.execute(
            select(FeatureModel).where(
                and_(
                    FeatureModel.user_id == user_id,
                    FeatureModel.is_active == True
                )
            )
        )
        all_features = list(all_features_result.scalars().all())
        
        feature_dicts = []
        for f in all_features:
            feature_dicts.append({
                "id": f.id,
                "feature_type": f.feature_type,
                "feature_value": f.feature_value,
                "confidence": f.confidence,
                "notes": f.notes
            })
        
        best_match, similarity = feature_merger.find_best_match(
            feature.feature_value,
            feature_dicts,
            feature_type=feature.feature_type,
            threshold=0.75
        )
        
        if best_match and similarity >= 0.75:
            existing_feature = None
            for f in all_features:
                if f.id == best_match["id"]:
                    existing_feature = f
                    break
            
            if existing_feature:
                existing_confidence = existing_feature.confidence
                new_confidence = (existing_confidence + feature.confidence) / 2
                
                existing_notes = existing_feature.notes or ""
                if existing_notes:
                    existing_notes += f"\n相似表达: {feature.feature_value} (相似度: {similarity:.2f})"
                else:
                    existing_notes = f"相似表达: {feature.feature_value} (相似度: {similarity:.2f})"
                
                existing_feature.confidence = new_confidence
                existing_feature.notes = existing_notes
                existing_feature.verification_count = (existing_feature.verification_count or 0) + 1
                existing_feature.last_verified_at = datetime.utcnow()
                existing_feature.updated_at = datetime.utcnow()
                
                if feature.reasoning:
                    if existing_feature.reasoning:
                        existing_feature.reasoning += f"\n{feature.reasoning}"
                    else:
                        existing_feature.reasoning = feature.reasoning
                
                await self.db.commit()
                await self.db.refresh(existing_feature)
                return existing_feature
        
        feature_model = FeatureModel(
            user_id=user_id,
            feature_type=feature.feature_type,
            feature_value=feature.feature_value,
            confidence=feature.confidence,
            source_message=feature.source_message,
            reasoning=feature.reasoning,
            evidence=feature.evidence
        )
        self.db.add(feature_model)
        await self.db.commit()
        await self.db.refresh(feature_model)

        if memo_base_service.is_enabled():
            await memo_base_service.save_feature(
                user_id, feature.feature_type, feature.feature_value,
                feature.confidence, feature.reasoning or "", feature.evidence or ""
            )

        await self._apply_decay_on_write(user_id)

        return feature_model

    async def _apply_decay_on_write(self, user_id: str) -> None:
        """写入时顺便应用衰减 - 减少数据库写入次数"""
        result = await self.db.execute(
            select(FeatureModel).where(
                and_(
                    FeatureModel.user_id == user_id,
                    FeatureModel.is_active == True,
                    FeatureModel.decay_enabled == True
                )
            )
        )
        features = list(result.scalars().all())

        needs_update = []
        for feature in features:
            decayed_confidence, is_expired = self.calculate_confidence_with_decay(
                feature.confidence,
                feature.feature_type,
                feature.created_at,
                feature.last_confirmed_at,
                stability_period_days=feature.stability_period_days or 30,
                decay_rate=feature.decay_rate or 0.05
            )

            if decayed_confidence < feature.confidence:
                feature.confidence = decayed_confidence
                feature.updated_at = datetime.utcnow()
                needs_update.append(feature)

            if is_expired:
                feature.is_active = False
                needs_update.append(feature)

        if needs_update:
            await self.db.commit()
    
    async def get_user_features(self, user_id: str, feature_type: str = None,
                           apply_decay: bool = True) -> Tuple[List[FeatureModel], Dict]:
        """获取用户特征

        Args:
            user_id: 用户ID
            feature_type: 可选，筛选特定类型
            apply_decay: 是否计算衰减（默认True，只读计算，不写数据库）

        Returns:
            (特征列表, 元数据，包含数据新鲜度等信息)
        """
        query = select(FeatureModel).where(
            and_(FeatureModel.user_id == user_id, FeatureModel.is_active == True)
        )

        if feature_type:
            query = query.where(FeatureModel.feature_type == feature_type)

        result = await self.db.execute(query.order_by(desc(FeatureModel.confidence)))
        features = list(result.scalars().all())

        metadata = {
            "total_count": len(features),
            "data_stale": False,
            "last_update": None,
            "needs_stability_eval": []
        }

        if features:
            latest_feature = max(features, key=lambda f: f.updated_at)
            metadata["last_update"] = latest_feature.updated_at.isoformat() if latest_feature.updated_at else None

            days_since_update = (datetime.utcnow() - latest_feature.updated_at).days if latest_feature.updated_at else 0
            if days_since_update > 90:
                metadata["data_stale"] = True

        if apply_decay:
            for feature in features:
                if feature.decay_enabled and feature.confidence > 0 and feature.stability_period_days > 0:
                    decayed_confidence, _ = self.calculate_confidence_with_decay(
                        feature.confidence,
                        feature.feature_type,
                        feature.created_at,
                        feature.last_confirmed_at,
                        stability_period_days=feature.stability_period_days or 30,
                        decay_rate=feature.decay_rate or 0.05
                    )
                    feature.confidence = decayed_confidence

                if feature.last_stability_eval_at is None and feature.decay_enabled:
                    metadata["needs_stability_eval"].append({
                        "id": feature.id,
                        "feature_type": feature.feature_type,
                        "feature_value": feature.feature_value
                    })

        return features, metadata

    async def add_relationship(self, user_id: str, person_name: str,
                              relationship_type: str, interaction_pattern: str = None,
                              confidence: float = 0.5, evidence: List[str] = None) -> Any:
        """添加社会关系"""
        from ..models.database import RelationshipModel

        existing = await self.db.execute(
            select(RelationshipModel).where(
                and_(
                    RelationshipModel.user_id == user_id,
                    RelationshipModel.person_name == person_name
                )
            )
        )
        existing_rel = existing.scalar_one_or_none()

        if existing_rel:
            existing_rel.relationship_type = relationship_type
            existing_rel.interaction_pattern = interaction_pattern
            existing_rel.confidence = max(confidence, existing_rel.confidence)
            existing_rel.evidence = evidence or existing_rel.evidence
            existing_rel.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing_rel)
            return existing_rel

        relationship = RelationshipModel(
            user_id=user_id,
            person_name=person_name,
            relationship_type=relationship_type,
            interaction_pattern=interaction_pattern,
            confidence=confidence,
            evidence=evidence or []
        )
        self.db.add(relationship)
        await self.db.commit()
        await self.db.refresh(relationship)

        return relationship

    async def get_user_relationships(self, user_id: str) -> List[Any]:
        """获取用户社会关系"""
        from ..models.database import RelationshipModel

        result = await self.db.execute(
            select(RelationshipModel).where(
                and_(
                    RelationshipModel.user_id == user_id,
                    RelationshipModel.is_active == True
                )
            ).order_by(desc(RelationshipModel.confidence))
        )
        return list(result.scalars().all())

    async def get_profile(self, user_id: str) -> Optional[ProfileModel]:
        """获取用户画像"""
        result = await self.db.execute(
            select(ProfileModel).where(ProfileModel.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_profile(self, user_id: str) -> ProfileModel:
        """更新用户画像"""
        user = await self.get_or_create_user(user_id)

        features, _ = await self.get_user_features(user_id, apply_decay=False)
        
        profile_data = {}
        for feature in features:
            if feature.feature_type not in profile_data:
                profile_data[feature.feature_type] = []
            profile_data[feature.feature_type].append({
                "value": feature.feature_value,
                "confidence": feature.confidence,
                "reasoning": feature.reasoning
            })
        
        summary = await self._generate_summary(user_id, features)
        
        existing_profile = await self.get_profile(user_id)
        
        if existing_profile:
            existing_profile.profile_data = profile_data
            existing_profile.summary = summary
            existing_profile.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing_profile)
            profile = existing_profile
        else:
            profile = ProfileModel(
                user_id=user_id,
                profile_data=profile_data,
                summary=summary
            )
            self.db.add(profile)
            await self.db.commit()
            await self.db.refresh(profile)

        if memo_base_service.is_enabled():
            await memo_base_service.save_user_profile(user_id, profile_data, summary)

        return profile
    
    async def _generate_summary(self, user_id: str, features: List[FeatureModel]) -> str:
        """生成画像摘要"""
        if not features:
            return "暂无足够信息生成画像"
        
        summary_parts = []
        
        mbti_features = [f for f in features if f.feature_type == "MBTI"]
        if mbti_features:
            summary_parts.append(f"性格类型: {mbti_features[0].feature_value}")
        
        behavior_features = [f for f in features if f.feature_type == "行为习惯"]
        if behavior_features:
            habits = [f.feature_value for f in behavior_features[:3]]
            summary_parts.append(f"行为特点: {', '.join(habits)}")
        
        intent_features = [f for f in features if f.feature_type == "潜在想法"]
        if intent_features:
            intents = [f.feature_value for f in intent_features[:2]]
            summary_parts.append(f"潜在想法: {', '.join(intents)}")
        
        return " | ".join(summary_parts)

    def calculate_confidence_with_decay(
        self,
        initial_confidence: float,
        feature_type: str,
        created_at: datetime,
        last_confirmed_at: datetime,
        stability_period_days: int = 30,
        decay_rate: float = 0.05,
        decay_config: Dict = None
    ) -> Tuple[float, bool]:
        """智能计算时间衰减后的置信度

        使用对数衰减函数：
        - 前期衰减很慢（特征稳定期）
        - 超过稳定期后衰减加速
        - 最终趋于最低置信度

        Args:
            initial_confidence: 初始置信度
            feature_type: 特征类型
            created_at: 特征创建时间
            last_confirmed_at: 最后确认时间
            stability_period_days: 该特征的稳定期天数（由LLM评估）
            decay_rate: 该特征的衰减率（由LLM评估）
            decay_config: 全局衰减配置

        Returns:
            (衰减后的置信度, 是否过期)
        """
        if decay_config is None:
            decay_config = DEFAULT_DECAY_CONFIG

        if not decay_config.get("enabled", True):
            return initial_confidence, False

        min_confidence = decay_config.get("min_confidence", 0.3)

        days_since_confirmed = (datetime.utcnow() - last_confirmed_at).days

        if days_since_confirmed <= stability_period_days:
            return initial_confidence, False

        days_after_stability = days_since_confirmed - stability_period_days

        log_decay = math.log1p(days_after_stability * decay_rate)

        confidence_range = initial_confidence - min_confidence
        decayed_confidence = initial_confidence - (log_decay * confidence_range * 0.3)

        decayed_confidence = max(decayed_confidence, min_confidence)

        is_expired = decayed_confidence <= min_confidence and days_since_confirmed > stability_period_days + 180

        return round(decayed_confidence, 3), is_expired

    async def apply_decay_to_features(self, user_id: str) -> Dict[str, Any]:
        """对用户的所有特征应用时间衰减

        Returns:
            包含更新和过期特征的统计
        """
        features, _ = await self.get_user_features(user_id, apply_decay=False)
        updated_count = 0
        expired_count = 0
        expired_features = []

        for feature in features:
            if not feature.decay_enabled:
                continue

            decayed_confidence, is_expired = self.calculate_confidence_with_decay(
                feature.confidence,
                feature.feature_type,
                feature.created_at,
                feature.last_confirmed_at
            )

            if decayed_confidence < feature.confidence:
                feature.confidence = decayed_confidence
                feature.updated_at = datetime.utcnow()
                updated_count += 1

            if is_expired:
                feature.is_active = False
                expired_count += 1
                expired_features.append({
                    "feature_type": feature.feature_type,
                    "feature_value": feature.feature_value,
                    "original_confidence": feature.confidence
                })

        if updated_count > 0 or expired_count > 0:
            await self.db.commit()

        return {
            "updated_count": updated_count,
            "expired_count": expired_count,
            "expired_features": expired_features
        }

    async def confirm_feature(self, user_id: str, feature_type: str, feature_value: str) -> bool:
        """当用户的言行再次确认了某个特征时，调用此方法提升置信度

        Returns:
            是否更新成功
        """
        result = await self.db.execute(
            select(FeatureModel).where(
                and_(
                    FeatureModel.user_id == user_id,
                    FeatureModel.feature_type == feature_type,
                    FeatureModel.feature_value == feature_value,
                    FeatureModel.is_active == True
                )
            )
        )
        feature = result.scalar_one_or_none()

        if not feature:
            return False

        confidence_boost = 0.1
        max_confidence = 0.95

        new_confidence = min(feature.confidence + confidence_boost, max_confidence)

        feature.confidence = new_confidence
        feature.last_confirmed_at = datetime.utcnow()
        feature.verification_count = (feature.verification_count or 0) + 1
        feature.last_verified_at = datetime.utcnow()
        feature.updated_at = datetime.utcnow()

        await self.db.commit()
        return True

    async def process_chat(self, user_id: str, message: str,
                           extract_features: bool = True,
                           deep_think: bool = False) -> Dict[str, Any]:
        """使用 LangGraph 处理聊天消息 - 优化版本，优先返回 LLM 响应"""
        from ..agents.chat_graph import ChatGraph

        chat_graph = ChatGraph(
            llm_provider=self.agent_orchestrator.llm,
            profile_service=self
        )

        # 第一步：快速获取 LLM 响应（不等待特征提取和画像更新）
        result = await chat_graph.ainvoke_fast(user_id, message, deep_think)

        # 第二步：如果需要提取特征，在后台异步处理（不阻塞响应）
        if extract_features and result.get("extracted_features"):
            # 创建后台任务异步处理特征提取和画像更新
            asyncio.create_task(
                self._background_process_features(
                    user_id, 
                    message, 
                    result.get("extracted_features", []),
                    result.get("conversation_history", [])
                )
            )

        return {
            "response": result["response"],
            "extracted_features": result.get("extracted_features", []),
            "think_content": result.get("think_content"),
            "profile_updated": result.get("profile_updated", False)
        }

    async def _background_process_features(
        self, 
        user_id: str, 
        message: str,
        extracted_features: List[Dict],
        conversation_history: List[Dict]
    ) -> None:
        """后台处理特征提取和用户画像更新"""
        try:
            # 注意：后台任务不需要保存到数据库，因为特征已经在 ainvoke 中提取
            # 这里只记录日志即可
            print(f"后台任务：为用户 {user_id} 处理了 {len(extracted_features)} 个特征（已在主流程保存）")
        except Exception as e:
            print(f"后台任务执行失败：{e}")

    async def process_chat_sync(self, user_id: str, message: str,
                           extract_features: bool = True,
                           deep_think: bool = False) -> Dict[str, Any]:
        """使用 LangGraph 处理聊天消息 - 同步版本（兼容旧版本）"""
        from ..agents.chat_graph import ChatGraph

        chat_graph = ChatGraph(
            llm_provider=self.agent_orchestrator.llm,
            profile_service=self
        )

        result = await chat_graph.ainvoke(user_id, message, deep_think)

        return {
            "response": result["response"],
            "extracted_features": result["extracted_features"],
            "think_content": result.get("think_content"),
            "profile_updated": result.get("profile_updated", False)
        }

    async def get_user_profile_detail(self, user_id: str) -> UserProfileDetail:
        """获取用户画像详情"""
        user = await self.get_or_create_user(user_id)
        profile = await self.get_profile(user_id)
        features, metadata = await self.get_user_features(user_id)
        conversations = await self.get_conversation_history(user_id, limit=20)

        feature_dicts = [
            {"feature_type": f.feature_type, "feature_value": f.feature_value, "confidence": f.confidence}
            for f in features
        ]
        kg_subgraph = knowledge_graph.get_user_subgraph(feature_dicts)
        
        summary = ProfileSummary(
            user_id=user_id,
            mbti=None,
            big_five={},
            behavior_habits=[],
            potential_thoughts=[],
            interests=[],
            values=[],
            confidence_score=0.0,
            total_features=len(features),
            conversation_count=len(conversations)
        )
        
        for f in features:
            if f.feature_type == "MBTI" and not summary.mbti:
                summary.mbti = f.feature_value
            elif f.feature_type == "大五人格":
                summary.big_five[f.feature_value] = f.confidence
            elif f.feature_type == "行为习惯":
                summary.behavior_habits.append(f.feature_value)
            elif f.feature_type == "潜在想法":
                summary.potential_thoughts.append(f.feature_value)
            elif f.feature_type == "兴趣爱好":
                summary.interests.append(f.feature_value)
            elif f.feature_type == "价值观":
                summary.values.append(f.feature_value)
        
        if features:
            summary.confidence_score = sum(f.confidence for f in features) / len(features)
        
        return UserProfileDetail(
            user_id=user_id,
            username=user.username,
            profile=ProfileResponse.from_orm(profile) if profile else None,
            features=[FeatureResponse.from_orm(f) for f in features],
            recent_conversations=[MessageResponse.from_orm(c) for c in conversations],
            knowledge_graph=kg_subgraph,
            summary=summary,
            metadata=metadata
        )
