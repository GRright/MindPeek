"""
知识图谱模块 - 混合推理模式（规则 + LLM）
结合心理学规则的高可靠性和 LLM 的灵活性
"""
import asyncio
import json
from typing import Dict, List, Optional, Tuple
from ..core.config import config_manager


class PersonalityKnowledgeBase:
    """人格心理学知识库"""

    MBTI_RELATIONS = {
        ("内向型", "社交回避"): ("implies", 0.85),
        ("内向型", "独处偏好"): ("implies", 0.9),
        ("外向型", "社交活跃"): ("implies", 0.85),
        ("外向型", "群体偏好"): ("implies", 0.8),
        ("直觉型", "抽象思维"): ("implies", 0.8),
        ("感觉型", "具体思维"): ("implies", 0.8),
        ("思考型", "理性决策"): ("implies", 0.85),
        ("情感型", "感性决策"): ("implies", 0.85),
        ("判断型", "计划性"): ("implies", 0.8),
        ("感知型", "灵活性"): ("implies", 0.8),
    }

    FEATURE_CATEGORIES = {
        "MBTI": ["内向型", "外向型", "直觉型", "感觉型", "思考型", "情感型", "判断型", "感知型"],
        "大五人格": ["开放性", "尽责性", "外向性", "宜人性", "神经质"],
        "行为习惯": ["夜猫子", "早起型", "线上社交偏好", "线下社交活跃", "冲动消费", "理性消费"],
        "兴趣爱好": ["科幻", "艺术", "运动", "音乐", "阅读", "游戏"],
        "价值观": ["诚信", "成就", "自我超越", "安全", "享乐"],
        "潜在想法": ["追求认可", "完美主义", "拖延行为", "社交回避"],
    }

    IMPLICIT_NEEDS = {
        "社交回避": {"潜在需求": ["安全感", "独处空间"], "可能问题": ["社交焦虑", "内向"]},
        "追求认可": {"潜在需求": ["自我价值", "归属感"], "可能问题": ["自尊问题"]},
        "完美主义": {"潜在需求": ["控制感", "成就感"], "可能问题": ["焦虑", "压力"]},
        "拖延行为": {"潜在需求": ["自主权"], "可能问题": ["执行力不足", "焦虑"]},
    }

    BEHAVIOR_TRAIT_MAPPING = {
        "夜猫子": ["开放性", "创造力"],
        "早起型": ["尽责性", "自律"],
        "线上社交偏好": ["内向型", "社交回避"],
        "线下社交活跃": ["外向型", "社交活跃"],
        "冲动消费": ["开放性", "神经质"],
        "理性消费": ["尽责性", "理性决策"],
    }


class HybridKnowledgeGraph:
    """混合知识图谱 - 结合规则推理和 LLM 推理"""

    def __init__(self):
        self.knowledge_base = PersonalityKnowledgeBase()
        self.llm_provider = None
        self._llm_initialized = False
        self._llm_available = False
    
    def _ensure_llm_provider(self):
        """确保 LLM 提供者已初始化（安全版本）"""
        if self._llm_initialized:
            return
        
        try:
            llm_config = config_manager.get_llm_config()
            if llm_config and hasattr(llm_config, 'api_key') and llm_config.api_key:
                from ..services.llm_provider import QwenProvider
                self.llm_provider = QwenProvider(llm_config)
                self._llm_available = True
                print("LLM 提供者初始化成功")
            else:
                print("LLM 配置不存在或 API Key 未设置")
                self._llm_available = False
        except Exception as e:
            print(f"初始化 LLM 失败（将使用规则推理）：{e}")
            self._llm_available = False
        finally:
            self._llm_initialized = True

    def get_user_subgraph(self, user_features: List[Dict]) -> Dict:
        """根据用户特征实时计算子图（同步版本，仅规则推理）"""
        try:
            if not user_features:
                return {"nodes": [], "edges": []}
            
            inferred_features = self._get_inferred_features_from_rules(user_features)
            return self._build_graph_with_inferences(user_features, inferred_features)
        except Exception as e:
            print(f"构建知识图谱失败：{e}")
            import traceback
            traceback.print_exc()
            return {"nodes": [], "edges": []}

    async def get_user_subgraph_async(self, user_features: List[Dict], 
                                       use_hybrid: bool = True,
                                       timeout: float = 10.0) -> Dict:
        """根据用户特征实时计算子图（异步版本，支持混合推理）
        
        Args:
            user_features: 用户特征列表
            use_hybrid: 是否使用混合推理（规则 + LLM）
            timeout: LLM 调用超时时间（秒）
        
        Returns:
            知识图谱节点和边的数据
        """
        try:
            if not user_features:
                return {"nodes": [], "edges": []}
            
            rule_based_features = self._get_inferred_features_from_rules(user_features)
            
            if not use_hybrid:
                return self._build_graph_with_inferences(user_features, rule_based_features)
            
            llm_inferred = {}
            if len(user_features) < 8 or len(rule_based_features) < 3:
                self._ensure_llm_provider()
                
                if self._llm_available and self.llm_provider:
                    try:
                        llm_inferred = await asyncio.wait_for(
                            self._infer_with_llm(user_features),
                            timeout=timeout
                        )
                        if not isinstance(llm_inferred, dict):
                            llm_inferred = {}
                    except asyncio.TimeoutError:
                        print("LLM 推理超时，使用规则推理结果")
                        llm_inferred = {}
                    except Exception as e:
                        print(f"LLM 推理失败：{e}")
                        llm_inferred = {}
            
            all_inferred = self._merge_inferred_features(rule_based_features, llm_inferred)
            return self._build_graph_with_inferences(user_features, all_inferred)
            
        except Exception as e:
            print(f"异步构建知识图谱失败：{e}")
            import traceback
            traceback.print_exc()
            return self._build_graph_with_inferences(user_features, {})

    def _build_graph_with_inferences(self, user_features: List[Dict], 
                                      inferred_features: Dict[str, Tuple[str, float]]) -> Dict:
        """构建包含推理特征的图谱"""
        nodes = []
        edges = []
        node_id_map = {}

        nodes.append({"id": 1, "node_name": "用户", "node_type": "user", "properties": {}})
        node_id_map["user"] = 1
        next_id = 2

        feature_types = set()
        for feature in user_features:
            feature_type = feature.get("feature_type", "")
            if feature_type:
                feature_types.add(feature_type)

        for feature_type in feature_types:
            nodes.append({
                "id": next_id,
                "node_name": feature_type,
                "node_type": "feature_type",
                "properties": {}
            })
            node_id_map[feature_type] = next_id
            edges.append({
                "source_id": 1,
                "target_id": next_id,
                "relation_type": "has_feature_type",
                "weight": 1.0
            })
            next_id += 1

        feature_node_ids = {}
        for feature in user_features:
            feature_type = feature.get("feature_type", "")
            feature_value = feature.get("feature_value", "")
            confidence = feature.get("confidence", 0.8)
            
            if not feature_type or not feature_value:
                continue

            type_node_id = node_id_map.get(feature_type)
            if type_node_id is None:
                continue

            nodes.append({
                "id": next_id,
                "node_name": feature_value,
                "node_type": "feature_value",
                "properties": {"confidence": confidence}
            })
            feature_node_ids[feature_value] = next_id
            edges.append({
                "source_id": type_node_id,
                "target_id": next_id,
                "relation_type": "is_a",
                "weight": confidence
            })
            next_id += 1

        for inferred_value, (source, conf) in inferred_features.items():
            if inferred_value in feature_node_ids:
                continue
            
            inferred_type = self._guess_feature_type(inferred_value)
            
            if inferred_type not in node_id_map:
                nodes.append({
                    "id": next_id,
                    "node_name": inferred_type,
                    "node_type": "inferred_type",
                    "properties": {}
                })
                node_id_map[inferred_type] = next_id
                edges.append({
                    "source_id": 1,
                    "target_id": next_id,
                    "relation_type": "has_inferred_type",
                    "weight": 0.9
                })
                next_id += 1
            
            nodes.append({
                "id": next_id,
                "node_name": inferred_value,
                "node_type": "inferred",
                "properties": {
                    "source": source,
                    "confidence": conf
                }
            })
            inferred_node_id = next_id
            next_id += 1
            
            edges.append({
                "source_id": node_id_map[inferred_type],
                "target_id": inferred_node_id,
                "relation_type": "is_a",
                "weight": conf
            })
            
            if source in feature_node_ids:
                edges.append({
                    "source_id": feature_node_ids[source],
                    "target_id": inferred_node_id,
                    "relation_type": "inferred_from",
                    "weight": conf
                })

        return {"nodes": nodes, "edges": edges}

    def _get_inferred_features_from_rules(self, user_features: List[Dict]) -> Dict[str, Tuple[str, float]]:
        """基于规则推理特征（支持模糊匹配）"""
        inferred = {}

        for feature in user_features:
            feature_value = feature.get("feature_value", "")
            if not feature_value:
                continue

            # MBTI 推理（模糊匹配）
            for mbti_pair, (relation, weight) in self.knowledge_base.MBTI_RELATIONS.items():
                for mbti_type in mbti_pair:
                    if mbti_type in feature_value or self._fuzzy_match(feature_value, mbti_type):
                        other = mbti_pair[1] if mbti_pair[0] == mbti_type else mbti_pair[0]
                        if relation == "implies":
                            if other not in inferred or inferred[other][1] < weight:
                                inferred[other] = (feature_value, weight)

            # 行为 - 特质映射（模糊匹配）
            for behavior, traits in self.knowledge_base.BEHAVIOR_TRAIT_MAPPING.items():
                if behavior in feature_value or self._fuzzy_match(feature_value, behavior):
                    for trait in traits:
                        if trait not in inferred or inferred[trait][1] < 0.7:
                            inferred[trait] = (feature_value, 0.7)

            # 潜在需求（模糊匹配）
            for need_key, need_data in self.knowledge_base.IMPLICIT_NEEDS.items():
                if need_key in feature_value or self._fuzzy_match(feature_value, need_key):
                    for need in need_data.get("潜在需求", []):
                        if need not in inferred or inferred[need][1] < 0.75:
                            inferred[need] = (feature_value, 0.75)

        return inferred

    def _fuzzy_match(self, text: str, keyword: str) -> bool:
        """模糊匹配关键词"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        if keyword_lower in text_lower:
            return True
        
        keyword_variants = {
            "内向型": ["内向", "introvert", "i人"],
            "外向型": ["外向", "extravert", "e人", "外向性较高", "外向性："],
            "社交回避": ["社交回避", "不喜欢与人打交道", "避免社交"],
            "独处偏好": ["独处", "喜欢独自", "享受独处"],
            "社交活跃": ["社交活跃", "喜欢社交", "线下社交活跃"],
        }
        
        if keyword in keyword_variants:
            for variant in keyword_variants[keyword]:
                if variant in text_lower:
                    return True
        
        return False

    async def _infer_with_llm(self, user_features: List[Dict]) -> Dict[str, Tuple[str, float]]:
        """使用 LLM 进行推理"""
        if not self.llm_provider:
            return {}

        feature_values = [f.get("feature_value", "") for f in user_features if f.get("feature_value")]
        
        if not feature_values:
            return {}

        prompt = f"""基于心理学常识，从以下用户特征可以推理出什么关联特征？

用户特征：{', '.join(feature_values[:10])}

请推理 3-5 个可能的关联特征，要求：
1. 基于心理学和生活常识
2. 避免过度推断
3. 置信度保守一些（0.5-0.8）
4. 只返回特征名称和置信度，不要解释

输出格式（JSON）：
{{
  "特征 1": 0.7,
  "特征 2": 0.65,
  "特征 3": 0.6
}}
"""

        try:
            response = await self.llm_provider.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            if not response:
                return {}
            
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                llm_result = json.loads(json_str)
                
                inferred = {}
                for feature, confidence in llm_result.items():
                    if isinstance(confidence, (int, float)) and 0 < confidence <= 1:
                        source = self._find_most_likely_source(feature, user_features)
                        inferred[feature] = (source, confidence * 0.8)
                return inferred
            return {}
                
        except json.JSONDecodeError as e:
            print(f"LLM 响应解析失败：{e}")
            return {}
        except Exception as e:
            print(f"LLM 推理错误：{e}")
            return {}

    def _find_most_likely_source(self, inferred_feature: str, 
                                  user_features: List[Dict]) -> str:
        """为推理特征找到最可能的来源特征"""
        if user_features:
            return user_features[0].get("feature_value", "未知")
        return "未知"

    def _merge_inferred_features(self, 
                                  rule_based: Dict[str, Tuple[str, float]],
                                  llm_based: Dict[str, Tuple[str, float]]) -> Dict[str, Tuple[str, float]]:
        """合并规则和 LLM 的推理结果"""
        merged = rule_based.copy()
        
        for feature, (source, conf) in llm_based.items():
            if feature in merged:
                old_conf = merged[feature][1]
                avg_conf = (old_conf * 0.7 + conf * 0.3)
                merged[feature] = (source, avg_conf)
            else:
                merged[feature] = (source, conf * 0.7)
        
        return merged

    def _get_inferred_features(self, feature_value: str) -> List[str]:
        """基于单个特征值推断相关特征（兼容接口）"""
        inferred = []
        
        for behavior, traits in self.knowledge_base.BEHAVIOR_TRAIT_MAPPING.items():
            if behavior == feature_value or behavior in feature_value:
                inferred.extend(traits)
        
        for need_key, need_data in self.knowledge_base.IMPLICIT_NEEDS.items():
            if feature_value == need_key or need_key in feature_value:
                inferred.extend(need_data.get("潜在需求", []))
        
        for mbti_pair, (relation, weight) in self.knowledge_base.MBTI_RELATIONS.items():
            if feature_value in mbti_pair or any(m in feature_value for m in mbti_pair):
                other = mbti_pair[1] if mbti_pair[0] == feature_value or mbti_pair[0] in feature_value else mbti_pair[0]
                if relation == "implies":
                    inferred.append(other)
        
        return list(set(inferred))[:5]

    def _guess_feature_type(self, feature_value: str) -> str:
        """猜测特征值的类型"""
        for category, values in self.knowledge_base.FEATURE_CATEGORIES.items():
            if feature_value in values:
                return category
        
        if any(kw in feature_value for kw in ["喜欢", "爱好", "兴趣"]):
            return "兴趣爱好"
        elif any(kw in feature_value for kw in ["习惯", "行为", "方式"]):
            return "行为习惯"
        elif any(kw in feature_value for kw in ["性格", "人格", "倾向"]):
            return "人格特质"
        else:
            return "推断特征"

    def get_feature_insights(self, user_features: List[Dict]) -> Dict:
        """基于用户特征生成洞察"""
        insights = {
            "personality_summary": "",
            "potential_needs": [],
            "behavior_patterns": [],
            "social_insights": ""
        }

        feature_values = [f.get("feature_value", "") for f in user_features]

        mbti_features = [f for f in feature_values if f in [
            "内向型", "外向型", "直觉型", "感觉型", "思考型", "情感型", "判断型", "感知型"
        ]]
        if mbti_features:
            insights["personality_summary"] = f"性格特点：{', '.join(mbti_features)}"

        for need_key, need_data in self.knowledge_base.IMPLICIT_NEEDS.items():
            if need_key in feature_values:
                insights["potential_needs"].extend(need_data.get("潜在需求", []))

        behavior_features = [f for f in feature_values if f in [
            "夜猫子", "早起型", "线上社交偏好", "线下社交活跃", "冲动消费", "理性消费"
        ]]
        if behavior_features:
            insights["behavior_patterns"] = behavior_features

        return insights


knowledge_graph = HybridKnowledgeGraph()
