"""
FeatureDiscovery Agent - 基于LangGraph的自主特征发现Agent
能够动态判断用户特征，自主决定记录哪些特征以及如何分类
"""
import json
from typing import Dict, List, Optional, Any
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from ..services.llm_provider import BaseLLMProvider


class FeatureDiscoveryState(BaseModel):
    """特征发现状态"""
    user_id: str = ""
    message: str = ""
    conversation_history: List[Dict[str, str]] = []
    existing_features: List[Dict[str, Any]] = []

    discovered_features: List[Dict[str, Any]] = []
    feature_decisions: List[Dict[str, Any]] = []

    new_category_suggestions: List[str] = []
    response: str = ""

    confidence_scores: Dict[str, float] = {}
    reasoning: str = ""

    errors: List[str] = []


class FeatureDiscoveryAgent:
    """特征发现Agent - 自主判断特征类型和记录方式"""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.graph = self._build_graph()

    PREDEFINED_CATEGORIES = [
        "MBTI", "大五人格", "行为习惯", "潜在想法",
        "兴趣爱好", "价值观", "情感状态", "生活偏好",
        "沟通风格", "思维模式", "社交特点", "工作风格"
    ]

    def _build_analysis_prompt(self, state: FeatureDiscoveryState) -> str:
        """构建分析提示词"""
        history_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
            for m in state.conversation_history[-10:]
        ])

        existing_features_text = ""
        if state.existing_features:
            feature_lines = []
            for f in state.existing_features[:15]:
                feature_lines.append(f"- {f.get('feature_type', '未知')}: {f.get('feature_value', '')} (置信度: {f.get('confidence', 0):.0%})")
            existing_features_text = "\n已有特征:\n" + "\n".join(feature_lines)

        categories_text = ", ".join(self.PREDEFINED_CATEGORIES)

        return f"""你是一个专业的用户特征分析师。你的任务是分析用户的对话，自主判断应该记录哪些特征。

## 你的能力
1. 可以识别预定义特征类型：{categories_text}
2. 可以发现新特征类型（如果用户透露的信息不适合已有分类）
3. 可以决定特征的置信度和记录方式

## 对话历史
{history_text}

{existing_features_text}

## 分析要求
1. 仔细分析用户最新消息中透露的个人信息
2. 判断哪些信息值得被记录为特征
3. 将新特征归类到最合适的预定义类型，或提出新的分类建议
4. 评估每个特征的置信度（基于对话中的证据充分程度）
5. 避免重复记录已有的相似特征

## 输出格式（JSON）
```json
{{
    "discovered_features": [
        {{
            "feature_type": "最合适的分类或'新类型:你的建议'",
            "feature_value": "具体的特征值",
            "confidence": 0.0-1.0,
            "reasoning": "为什么认为这个特征重要",
            "evidence": ["对话中的具体证据1", "证据2"]
        }}
    ],
    "reasoning": "整体分析思路"
}}
```

请直接返回JSON，不要有其他内容。"""

    async def analyze_message(self, state: FeatureDiscoveryState) -> FeatureDiscoveryState:
        """分析消息，发现特征"""
        try:
            prompt = self._build_analysis_prompt(state)

            messages = [{"role": "system", "content": "你是一个专业的用户特征分析师。"}]

            for conv in state.conversation_history[-6:]:
                messages.append({"role": conv["role"], "content": conv["content"]})

            messages.append({"role": "user", "content": f"请分析这条消息中的用户特征：{state.message}\n\n{prompt}"})

            response = await self.llm.chat(messages)

            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    result = json.loads(response[start:end])
                    state.discovered_features = result.get("discovered_features", [])
                    state.reasoning = result.get("reasoning", "")
            except json.JSONDecodeError:
                state.errors.append("解析特征分析结果失败")

        except Exception as e:
            state.errors.append(f"分析消息失败: {str(e)}")

        return state

    async def validate_features(self, state: FeatureDiscoveryState) -> FeatureDiscoveryState:
        """验证和过滤特征"""
        try:
            if not state.discovered_features:
                return state

            validated_features = []
            for feature in state.discovered_features:
                if feature.get("confidence", 0) < 0.5:
                    continue

                feature_type = feature.get("feature_type", "")
                feature_value = feature.get("feature_value", "")

                if not feature_type or not feature_value:
                    continue

                if "新类型" in feature_type:
                    new_category = feature_type.replace("新类型:", "").strip()
                    if new_category:
                        state.new_category_suggestions.append(new_category)
                        feature["feature_type"] = new_category
                    else:
                        continue

                is_duplicate = False
                for existing in state.existing_features:
                    if (existing.get("feature_type") == feature_type and
                        existing.get("feature_value") == feature_value):
                        is_duplicate = True
                        if feature.get("confidence", 0) > existing.get("confidence", 0):
                            feature["is_update"] = True
                            validated_features.append(feature)
                        break

                if not is_duplicate:
                    validated_features.append(feature)

            state.discovered_features = validated_features

        except Exception as e:
            state.errors.append(f"验证特征失败: {str(e)}")

        return state

    async def decide_storage(self, state: FeatureDiscoveryState) -> FeatureDiscoveryState:
        """决定特征存储策略"""
        try:
            for feature in state.discovered_features:
                confidence = feature.get("confidence", 0)

                if confidence >= 0.8:
                    feature["storage_priority"] = "high"
                    feature["aggregation_needed"] = False
                elif confidence >= 0.6:
                    feature["storage_priority"] = "medium"
                    feature["aggregation_needed"] = True
                else:
                    feature["storage_priority"] = "low"
                    feature["aggregation_needed"] = True

                feature_type = feature.get("feature_type", "")
                if feature_type in ["MBTI", "大五人格"]:
                    feature["aggregation_needed"] = False
                    feature["storage_priority"] = "high"
                elif feature_type in ["行为习惯", "潜在想法"]:
                    feature["aggregation_needed"] = True

            state.feature_decisions = state.discovered_features

        except Exception as e:
            state.errors.append(f"决定存储策略失败: {str(e)}")

        return state

    async def generate_insight(self, state: FeatureDiscoveryState) -> FeatureDiscoveryState:
        """生成洞察报告"""
        try:
            if not state.discovered_features:
                state.response = "本次对话未发现新的用户特征。"
                return state

            insights = []
            for f in state.discovered_features:
                insights.append({
                    "类型": f.get("feature_type", "未知"),
                    "值": f.get("feature_value", ""),
                    "置信度": f"{f.get('confidence', 0):.0%}",
                    "依据": f.get("reasoning", "")[:50] + "..."
                })

            state.response = f"发现 {len(state.discovered_features)} 个新特征:\n" + \
                           "\n".join([f"- {i['类型']}: {i['值']} (置信度: {i['置信度']})" for i in insights])

        except Exception as e:
            state.errors.append(f"生成洞察失败: {str(e)}")

        return state

    def _build_graph(self) -> StateGraph:
        """构建特征发现图"""
        workflow = StateGraph(FeatureDiscoveryState)

        workflow.add_node("analyze", self.analyze_message)
        workflow.add_node("validate", self.validate_features)
        workflow.add_node("decide_storage", self.decide_storage)
        workflow.add_node("generate_insight", self.generate_insight)

        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "validate")
        workflow.add_edge("validate", "decide_storage")
        workflow.add_edge("decide_storage", "generate_insight")
        workflow.add_edge("generate_insight", END)

        return workflow.compile()

    async def discover(
        self,
        user_id: str,
        message: str,
        conversation_history: List[Dict[str, str]],
        existing_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """执行特征发现"""
        initial_state = FeatureDiscoveryState(
            user_id=user_id,
            message=message,
            conversation_history=conversation_history,
            existing_features=existing_features
        )

        final_state = await self.graph.ainvoke(initial_state)

        return {
            "discovered_features": final_state.discovered_features,
            "feature_decisions": final_state.feature_decisions,
            "new_category_suggestions": final_state.new_category_suggestions,
            "response": final_state.response,
            "reasoning": final_state.reasoning,
            "errors": final_state.errors
        }


class FeatureCorrelationAgent:
    """特征关联分析Agent - 发现特征之间的关联"""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    async def analyze_correlations(
        self,
        user_id: str,
        new_features: List[Dict[str, Any]],
        existing_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析特征关联"""
        if not existing_features:
            return {"inferred_features": [], "correlations": []}

        prompt = f"""你是一个特征关联分析专家。请分析以下用户特征，发现潜在的关联和推断。

## 已有特征
{json.dumps(existing_features, ensure_ascii=False, indent=2)}

## 新发现的特征
{json.dumps(new_features, ensure_ascii=False, indent=2)}

## 分析要求
1. 找出新特征与已有特征之间的关联
2. 基于关联推断用户可能具备的其他特征
3. 解释推断的依据

## 输出格式（JSON）
```json
{{
    "correlations": [
        {{
            "feature_a": "特征A",
            "feature_b": "特征B",
            "relationship": "关联描述",
            "strength": 0.0-1.0
        }}
    ],
    "inferred_features": [
        {{
            "inferred_feature": "推断的特征",
            "based_on": ["依据的特征1", "特征2"],
            "confidence": 0.0-1.0,
            "reasoning": "推断理由"
        }}
    ]
}}
```

请直接返回JSON。"""

        try:
            messages = [
                {"role": "system", "content": "你是一个专业的特征关联分析专家。"},
                {"role": "user", "content": prompt}
            ]

            response = await self.llm.chat(messages)

            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                result = json.loads(response[start:end])
                return result

        except Exception as e:
            return {"inferred_features": [], "correlations": [], "error": str(e)}

        return {"inferred_features": [], "correlations": []}


class LatentIntentAgent:
    """隐性需求发现Agent - 识别用户潜在需求和意图"""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    async def discover_latent_intents(
        self,
        user_id: str,
        message: str,
        conversation_history: List[Dict[str, str]],
        existing_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """发现用户的隐性需求"""
        history_text = "\n".join([
            f"{'用户' if m.get('role') == 'user' else '助手'}: {m.get('content', '')}"
            for m in conversation_history[-15:]
        ])

        features_text = json.dumps(existing_features[:20], ensure_ascii=False, indent=2)

        system_prompt = f"""你是一个专业的需求分析师。你的任务是发现用户对话中透露的隐性需求。

## 什么是隐性需求？
隐性需求是指用户没有直接表达，但可以从其言行中推断出来的潜在需求。
例如：
- 用户说"外面的雨把伞弄坏了" → 可能需要购买新伞
- 用户抱怨"上班总是迟到" → 可能需要时间管理工具
- 用户说"最近总是睡不着" → 可能需要助眠产品或放松服务

## 对话历史
{history_text}

## 用户当前消息
{message}

## 用户已有特征
{features_text}

## 分析要求
1. 仔细分析对话历史，发现用户透露的隐性问题或需求
2. 结合用户已有特征推断可能的潜在需求
3. 识别用户的痛点和未满足的需求
4. 推断用户可能的行为模式和未来可能的行动

## 隐性需求类型
- 生活需求：日常用品、生活服务
- 健康需求：医疗、保健、运动健身
- 工作需求：效率工具、技能提升
- 社交需求：人际交往、社区参与
- 情感需求：心理支持、娱乐休闲
- 学习需求：教育培训、知识获取

## 输出格式（JSON）
```json
{{
    "latent_needs": [
        {{
            "need_category": "需求类别",
            "need_description": "需求描述",
            "trigger_event": "触发事件或线索",
            "confidence": 0.0-1.0,
            "reasoning": "推断理由",
            "urgency": "high/medium/low",
            "potential_actions": ["可能的行动1", "行动2"]
        }}
    ],
    "behavior_predictions": [
        {{
            "prediction": "行为预测",
            "based_on": ["依据1", "依据2"],
            "confidence": 0.0-1.0
        }}
    ],
    "insights": "整体洞察..."
}}
```

请直接返回JSON，不要有其他内容。"""

        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "请分析这条消息中的隐性需求"}
            ]

            response = await self.llm.chat(messages)

            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                result = json.loads(response[start:end])
                return {
                    "latent_needs": result.get("latent_needs", []),
                    "behavior_predictions": result.get("behavior_predictions", []),
                    "insights": result.get("insights", ""),
                    "raw_response": response
                }

        except Exception as e:
            return {
                "latent_needs": [],
                "behavior_predictions": [],
                "insights": "",
                "error": str(e)
            }

        return {
            "latent_needs": [],
            "behavior_predictions": [],
            "insights": ""
        }
