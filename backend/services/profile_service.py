"""
用户画像服务层
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from ..models.database import UserModel, ProfileModel, ConversationModel, FeatureModel
from ..models.schemas import (
    FeatureCreate, FeatureResponse, MessageCreate, MessageResponse,
    ProfileResponse, ProfileSummary, UserProfileDetail
)
from ..agents.agent_engine import AgentOrchestrator
from ..knowledge_graph.graph import knowledge_graph
from ..core.config import config_manager
from .memo_base_service import memo_base_service


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
        """添加特征"""
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
                existing.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        
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
        
        knowledge_graph.add_user_feature(
            user_id, feature.feature_type, feature.feature_value,
            feature.confidence, feature.source_message
        )

        if memo_base_service.is_enabled():
            await memo_base_service.save_feature(
                user_id, feature.feature_type, feature.feature_value,
                feature.confidence, feature.reasoning or "", feature.evidence or ""
            )

        return feature_model
    
    async def get_user_features(self, user_id: str, feature_type: str = None) -> List[FeatureModel]:
        """获取用户特征"""
        query = select(FeatureModel).where(
            and_(FeatureModel.user_id == user_id, FeatureModel.is_active == True)
        )
        
        if feature_type:
            query = query.where(FeatureModel.feature_type == feature_type)
        
        result = await self.db.execute(query.order_by(desc(FeatureModel.confidence)))
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
        
        features = await self.get_user_features(user_id)
        
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
    
    async def extract_features_from_conversation(self, user_id: str, 
                                                   new_message: str) -> List[FeatureCreate]:
        """从对话中提取特征"""
        conversations = await self.get_conversation_history(user_id, limit=10)
        
        messages = [{"role": c.role, "content": c.content} for c in conversations]
        messages.append({"role": "user", "content": new_message})
        
        existing_features = {}
        features = await self.get_user_features(user_id)
        for f in features:
            if f.feature_type not in existing_features:
                existing_features[f.feature_type] = []
            existing_features[f.feature_type].append({
                "value": f.feature_value,
                "confidence": f.confidence
            })
        
        extracted_features = await self.agent_orchestrator.extract_features(
            messages, existing_features
        )
        
        feature_creates = []
        for f in extracted_features:
            feature_create = FeatureCreate(
                feature_type=f["type"],
                feature_value=f["value"],
                confidence=f["confidence"],
                source_message=new_message,
                reasoning=f.get("reasoning", ""),
                evidence=f.get("details", [])
            )
            feature_creates.append(feature_create)
        
        return feature_creates
    
    async def process_chat(self, user_id: str, message: str, 
                           extract_features: bool = True) -> Dict[str, Any]:
        """处理聊天消息"""
        await self.add_conversation(user_id, MessageCreate(
            role="user",
            content=message
        ))
        
        extracted_features = []
        if extract_features:
            extracted_features = await self.extract_features_from_conversation(user_id, message)
            
            for feature in extracted_features:
                await self.add_feature(user_id, feature)
        
        await self.update_profile(user_id)
        
        correlation_result = await self.agent_orchestrator.update_with_correlation(
            user_id,
            [{"type": f.feature_type, "value": f.feature_value, "confidence": f.confidence} 
             for f in extracted_features],
            {}  # existing_features
        )
        
        for inferred in correlation_result.get("inferred_features", []):
            await self.add_feature(user_id, FeatureCreate(
                feature_type=inferred["type"],
                feature_value=inferred["value"],
                confidence=inferred["confidence"],
                source_message="知识图谱推断",
                reasoning=inferred["reasoning"]
            ))
        
        return {
            "extracted_features": extracted_features,
            "inferred_features": correlation_result.get("inferred_features", []),
            "conflicts": correlation_result.get("conflicts", [])
        }
    
    async def get_user_profile_detail(self, user_id: str) -> UserProfileDetail:
        """获取用户画像详情"""
        user = await self.get_or_create_user(user_id)
        profile = await self.get_profile(user_id)
        features = await self.get_user_features(user_id)
        conversations = await self.get_conversation_history(user_id, limit=20)
        
        kg_subgraph = knowledge_graph.get_user_subgraph(user_id)
        
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
            summary=summary
        )
