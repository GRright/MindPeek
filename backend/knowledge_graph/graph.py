"""
知识图谱模块 - 基于预定义心理学知识的关联推理
用户特征从数据库实时获取，不再重复存储
"""
from typing import Dict, List


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


class KnowledgeGraph:
    """知识图谱核心类 - 实时计算，不存储用户数据"""

    def __init__(self):
        self.knowledge_base = PersonalityKnowledgeBase()

    def get_user_subgraph(self, user_features: List[Dict]) -> Dict:
        """根据用户特征实时计算子图

        Args:
            user_features: 用户特征列表，每项包含 feature_type 和 feature_value

        Returns:
            知识图谱节点和边的数据
        """
        nodes = []
        edges = []
        node_id_map = {}

        nodes.append({"id": 1, "node_name": "用户", "node_type": "user", "properties": {}})
        node_id_map["user"] = 1
        next_id = 2

        feature_types = set()
        for feature in user_features:
            feature_type = feature.get("feature_type", "")
            feature_value = feature.get("feature_value", "")
            if feature_type and feature_value:
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

        for feature in user_features:
            feature_type = feature.get("feature_type", "")
            feature_value = feature.get("feature_value", "")
            if not feature_type or not feature_value:
                continue

            type_node_id = node_id_map.get(feature_type)
            if type_node_id is None:
                continue

            nodes.append({
                "id": next_id,
                "node_name": feature_value,
                "node_type": "feature_value",
                "properties": {}
            })
            edges.append({
                "source_id": type_node_id,
                "target_id": next_id,
                "relation_type": "is_a",
                "weight": 0.8
            })
            next_id += 1

            inferred_features = self._get_inferred_features(feature_value)
            for inferred in inferred_features:
                nodes.append({
                    "id": next_id,
                    "node_name": inferred,
                    "node_type": "inferred",
                    "properties": {}
                })
                edges.append({
                    "source_id": next_id - 1,
                    "target_id": next_id,
                    "relation_type": "implies",
                    "weight": 0.7
                })
                next_id += 1

        return {"nodes": nodes, "edges": edges}

    def _get_inferred_features(self, feature_value: str) -> List[str]:
        """基于特征值推断相关特征"""
        inferred = []

        for behavior, traits in self.knowledge_base.BEHAVIOR_TRAIT_MAPPING.items():
            if behavior == feature_value:
                inferred.extend(traits)

        for need_key, need_data in self.knowledge_base.IMPLICIT_NEEDS.items():
            if feature_value == need_key:
                inferred.extend(need_data.get("潜在需求", []))

        for mbti_pair, (relation, weight) in self.knowledge_base.MBTI_RELATIONS.items():
            if feature_value in mbti_pair:
                other = mbti_pair[1] if mbti_pair[0] == feature_value else mbti_pair[0]
                if relation == "implies":
                    inferred.append(other)

        return list(set(inferred))[:5]

    def find_correlations(self, user_features: List[Dict]) -> Dict:
        """发现用户特征之间的关联"""
        correlations = []
        conflicts = []

        feature_values = [f.get("feature_value", "") for f in user_features]

        for feature in user_features:
            feature_value = feature.get("feature_value", "")
            inferred = self._get_inferred_features(feature_value)

            for inf in inferred:
                if inf in feature_values:
                    correlations.append({
                        "source": feature_value,
                        "target": inf,
                        "relation": "correlates_with",
                        "weight": 0.7
                    })

        return {"correlations": correlations, "conflicts": conflicts}

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
            insights["personality_summary"] = f"性格特点: {', '.join(mbti_features)}"

        for need_key, need_data in self.knowledge_base.IMPLICIT_NEEDS.items():
            if need_key in feature_values:
                insights["potential_needs"].extend(need_data.get("潜在需求", []))

        behavior_features = [f for f in feature_values if f in [
            "夜猫子", "早起型", "线上社交偏好", "线下社交活跃", "冲动消费", "理性消费"
        ]]
        if behavior_features:
            insights["behavior_patterns"] = behavior_features

        return insights


knowledge_graph = KnowledgeGraph()
