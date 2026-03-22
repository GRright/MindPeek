"""
LangGraph 聊天Agent - 基于图的对话处理流程
"""
import json
from typing import Dict, List, Optional, Any
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from ..services.llm_provider import LLMProviderFactory, BaseLLMProvider
from ..services.profile_service import ProfileService
from .feature_discovery import FeatureDiscoveryAgent, FeatureCorrelationAgent
from .async_orchestrator import AsyncAgentOrchestrator, TaskType, get_orchestrator


class ChatState(BaseModel):
    """聊天状态"""
    user_id: str = ""
    message: str = ""
    conversation_history: List[Dict[str, str]] = []
    user_context: str = ""
    has_context: bool = False
    use_personalization: bool = True
    response: str = ""
    extracted_features: List[Dict] = []
    think_content: Optional[str] = None
    deep_think: bool = False
    profile_updated: bool = False
    errors: List[str] = []


class ChatGraph:
    """LangGraph 聊天图"""

    def __init__(self, llm_provider: BaseLLMProvider, profile_service: ProfileService):
        self.llm = llm_provider
        self.profile_service = profile_service
        self.feature_discovery_agent = FeatureDiscoveryAgent(llm_provider)
        self.feature_correlation_agent = FeatureCorrelationAgent(llm_provider)
        self.async_orchestrator = get_orchestrator(llm_provider)
        self.graph = self._build_graph()

    def _build_personalization_prompt(self, state: ChatState) -> str:
        """构建个性化提示词"""
        if state.has_context and state.use_personalization:
            return f"""你是一个友善的AI助手，正在与用户进行对话。

## 用户信息
你已经了解了该用户的一些特征信息：{state.user_context}

## 回复要求
1. 首先判断用户的问题是否与个人化话题相关（如性格、情感、偏好、习惯、自我认知等）
2. 如果相关，结合用户特征给出个性化回答
3. 如果是通用知识性问题（如定义、解释、方法、计算等），直接给出清晰回答
4. 保持回复简洁，自然，像朋友间的对话

请直接回答，不需要在回复中说明你的判断过程。"""
        else:
            return """你是一个友善的AI助手，正在与用户进行对话。

## 回复要求
1. 如果是个人化话题（性格、情感、偏好、习惯、自我认知等），直接回答
2. 如果是通用知识性问题（如定义、解释、方法、计算等），直接给出清晰回答
3. 保持回复简洁，自然，像朋友间的对话

请直接回答。"""

    def _should_use_personalization(self, state: ChatState) -> str:
        """判断是否使用个性化"""
        message_lower = state.message.lower()

        general_keywords = [
            "什么是", "如何", "怎么", "为什么", "介绍一下",
            "请问", "告诉我", "解释一下", "计算", "定义",
            "搜索", "查找", "翻译", "天气", "时间",
            "写作文", "写文章", "帮我写", "代码", "程序",
            "math", "what is", "how to", "why", "explain",
            "translate", "weather", "time", "calculate"
        ]

        personal_keywords = [
            "我喜欢", "我的", "我觉得", "我想", "我最近",
            "我的性格", "我是", "我的爱好", "我的习惯",
            "你觉得我", "我是怎么样的人", "我的特点",
            "我喜欢做", "我经常", "我总是", "我有时候",
            "我的问题是", "我的烦恼", "我感到", "我的心情"
        ]

        for keyword in personal_keywords:
            if keyword in message_lower:
                return "use_personalization"

        for keyword in general_keywords:
            if keyword in message_lower:
                return "general"

        return "use_personalization"

    async def save_user_message(self, state: ChatState) -> ChatState:
        """保存用户消息"""
        try:
            await self.profile_service.add_conversation(
                state.user_id,
                {"role": "user", "content": state.message}
            )
        except Exception as e:
            state.errors.append(f"保存用户消息失败: {str(e)}")
        return state

    async def load_context(self, state: ChatState) -> ChatState:
        """加载用户上下文"""
        try:
            features, _ = await self.profile_service.get_user_features(state.user_id)

            if not features:
                state.has_context = False
                state.user_context = ""
                return state

            context_parts = ["\n## 用户画像信息（供参考）"]

            mbti_features = [f for f in features if f.feature_type == "MBTI" and f.confidence >= 0.6]
            if mbti_features:
                mbti = mbti_features[0]
                context_parts.append(f"- 性格类型(MBTI): {mbti.feature_value}（置信度: {mbti.confidence:.0%}）")

            big_five_features = [f for f in features if f.feature_type == "大五人格" and f.confidence >= 0.6]
            if big_five_features:
                traits = []
                for f in big_five_features[:3]:
                    trait_name = f.feature_value.split(':')[0] if ':' in f.feature_value else f.feature_value
                    traits.append(f"{trait_name}({f.confidence:.0%})")
                if traits:
                    context_parts.append(f"- 人格特质: {', '.join(traits)}")

            behavior_features = [f for f in features if f.feature_type == "行为习惯" and f.confidence >= 0.6]
            if behavior_features:
                habits = [f.feature_value for f in behavior_features[:3]]
                context_parts.append(f"- 行为习惯: {', '.join(habits)}")

            interest_features = [f for f in features if f.feature_type == "兴趣爱好" and f.confidence >= 0.6]
            if interest_features:
                interests = [f.feature_value for f in interest_features[:3]]
                context_parts.append(f"- 兴趣爱好: {', '.join(interests)}")

            value_features = [f for f in features if f.feature_type == "价值观" and f.confidence >= 0.6]
            if value_features:
                values = [f.feature_value for f in value_features[:2]]
                context_parts.append(f"- 价值观: {', '.join(values)}")

            intent_features = [f for f in features if f.feature_type == "潜在想法" and f.confidence >= 0.7]
            if intent_features:
                intents = [f.feature_value for f in intent_features[:2]]
                context_parts.append(f"- 潜在需求: {', '.join(intents)}")

            if len(context_parts) > 1:
                state.user_context = "\n".join(context_parts) + "\n\n请结合以上用户画像信息，提供更个性化的回答。"
                state.has_context = True
            else:
                state.has_context = False
                state.user_context = ""

        except Exception as e:
            state.errors.append(f"加载用户上下文失败: {str(e)}")
            state.has_context = False

        return state

    async def load_conversation_history(self, state: ChatState) -> ChatState:
        """加载对话历史"""
        try:
            conversations = await self.profile_service.get_conversation_history(
                state.user_id, limit=10
            )
            state.conversation_history = [
                {"role": c.role, "content": c.content}
                for c in conversations[-6:]
            ]
        except Exception as e:
            state.errors.append(f"加载对话历史失败: {str(e)}")
            state.conversation_history = []
        return state

    async def generate_personalized_response(self, state: ChatState) -> ChatState:
        """生成个性化回复"""
        try:
            system_prompt = self._build_personalization_prompt(state)

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(state.conversation_history)
            messages.append({"role": "user", "content": state.message})

            response = await self.llm.chat(messages)
            state.response = response

        except Exception as e:
            state.errors.append(f"生成回复失败: {str(e)}")
            state.response = f"抱歉，生成回复时出现错误: {str(e)}"

        return state

    async def generate_general_response(self, state: ChatState) -> ChatState:
        """生成通用回复（不使用个性化）"""
        state.use_personalization = False
        return await self.generate_personalized_response(state)

    async def extract_features(self, state: ChatState) -> ChatState:
        """使用FeatureDiscovery Agent提取用户特征"""
        try:
            existing_features, feature_metadata = await self.profile_service.get_user_features(state.user_id)
            existing_features_data = [
                {
                    "feature_type": f.feature_type,
                    "feature_value": f.feature_value,
                    "confidence": f.confidence
                }
                for f in existing_features
            ]

            discovery_result = await self.feature_discovery_agent.discover(
                user_id=state.user_id,
                message=state.message,
                conversation_history=state.conversation_history,
                existing_features=existing_features_data
            )

            state.extracted_features = discovery_result.get("discovered_features", [])

            for feature in state.extracted_features:
                from ..models.schemas import FeatureCreate
                feature_create = FeatureCreate(
                    feature_type=feature.get("feature_type", "未知"),
                    feature_value=feature.get("feature_value", ""),
                    confidence=feature.get("confidence", 0.5),
                    source_message=state.message,
                    reasoning=feature.get("reasoning", ""),
                    evidence=feature.get("evidence", [])
                )
                added_feature = await self.profile_service.add_feature(state.user_id, feature_create)

                if self.async_orchestrator and added_feature:
                    await self.async_orchestrator.submit_task(
                        task_type=TaskType.STABILITY_EVALUATION,
                        user_id=state.user_id,
                        input_data={
                            "feature_type": feature.get("feature_type", ""),
                            "feature_value": feature.get("feature_value", ""),
                            "features": existing_features_data
                        },
                        priority=-1
                    )

            if discovery_result.get("new_category_suggestions"):
                state.errors.append(f"建议新特征类型: {discovery_result['new_category_suggestions']}")

        except Exception as e:
            state.errors.append(f"提取特征失败: {str(e)}")

        return state

    async def update_profile(self, state: ChatState) -> ChatState:
        """更新用户画像并关联分析"""
        try:
            await self.profile_service.update_profile(state.user_id)

            if state.extracted_features:
                existing_features, _ = await self.profile_service.get_user_features(state.user_id)
                existing_features_data = [
                    {
                        "feature_type": f.feature_type,
                        "feature_value": f.feature_value,
                        "confidence": f.confidence
                    }
                    for f in existing_features
                ]

                correlation_result = await self.feature_correlation_agent.analyze_correlations(
                    state.user_id,
                    state.extracted_features,
                    existing_features_data
                )

                for inferred in correlation_result.get("inferred_features", []):
                    from ..models.schemas import FeatureCreate
                    feature_create = FeatureCreate(
                        feature_type="推断特征",
                        feature_value=inferred.get("inferred_feature", ""),
                        confidence=inferred.get("confidence", 0.5),
                        source_message="知识图谱关联推断",
                        reasoning=inferred.get("reasoning", "")
                    )
                    await self.profile_service.add_feature(state.user_id, feature_create)

                if self.async_orchestrator:
                    await self.async_orchestrator.submit_task(
                        task_type=TaskType.LATENT_INTENT,
                        user_id=state.user_id,
                        input_data={
                            "message": state.message,
                            "conversation_history": state.conversation_history,
                            "existing_features": existing_features_data
                        },
                        priority=0
                    )

            state.profile_updated = True
        except Exception as e:
            state.errors.append(f"更新画像失败: {str(e)}")
        return state

    async def save_assistant_message(self, state: ChatState) -> ChatState:
        """保存助手回复"""
        try:
            await self.profile_service.add_conversation(
                state.user_id,
                {"role": "assistant", "content": state.response}
            )
        except Exception as e:
            state.errors.append(f"保存助手回复失败: {str(e)}")
        return state

    async def deep_think_analysis(self, state: ChatState) -> ChatState:
        """异步提交深度思考分析任务"""
        if not state.deep_think:
            return state

        try:
            features = await self.profile_service.get_user_features(state.user_id)
            conversations = await self.profile_service.get_conversation_history(state.user_id, limit=20)

            user_features_data = [
                {
                    "feature_type": f.feature_type,
                    "feature_value": f.feature_value,
                    "confidence": f.confidence
                }
                for f in features
            ]

            conversation_data = [
                {"role": c.role, "content": c.content}
                for c in conversations
            ]

            if self.async_orchestrator:
                task_id = await self.async_orchestrator.submit_task(
                    task_type=TaskType.DEEP_THINK,
                    user_id=state.user_id,
                    input_data={
                        "message": state.message,
                        "conversation_history": conversation_data,
                        "user_features": user_features_data
                    },
                    priority=1
                )
                state.think_content = f"深度思考任务已提交: {task_id}"
            else:
                state.think_content = "异步任务系统未初始化"

        except Exception as e:
            state.errors.append(f"提交深度思考任务失败: {str(e)}")

        return state

    def route_decision(self, state: ChatState) -> str:
        """路由决策 - 决定使用哪个分支"""
        return self._should_use_personalization(state)

    def should_deep_think(self, state: ChatState) -> str:
        """是否进行深度思考"""
        return "deep_think" if state.deep_think else "skip_deep_think"

    def _build_graph(self) -> StateGraph:
        """构建状态图"""
        workflow = StateGraph(ChatState)

        workflow.add_node("save_user_message", self.save_user_message)
        workflow.add_node("load_context", self.load_context)
        workflow.add_node("load_history", self.load_conversation_history)
        workflow.add_node("generate_personalized", self.generate_personalized_response)
        workflow.add_node("generate_general", self.generate_general_response)
        workflow.add_node("extract_features", self.extract_features)
        workflow.add_node("update_profile", self.update_profile)
        workflow.add_node("save_assistant_message", self.save_assistant_message)
        workflow.add_node("deep_think_analysis", self.deep_think_analysis)

        workflow.set_entry_point("save_user_message")

        workflow.add_edge("save_user_message", "load_context")
        workflow.add_edge("load_context", "load_history")

        workflow.add_conditional_edges(
            "load_history",
            self.route_decision,
            {
                "use_personalization": "generate_personalized",
                "general": "generate_general"
            }
        )

        workflow.add_edge("generate_personalized", "extract_features")
        workflow.add_edge("generate_general", "extract_features")

        workflow.add_edge("extract_features", "update_profile")

        workflow.add_conditional_edges(
            "update_profile",
            self.should_deep_think,
            {
                "deep_think": "deep_think_analysis",
                "skip_deep_think": "save_assistant_message"
            }
        )

        workflow.add_edge("deep_think_analysis", "save_assistant_message")
        workflow.add_edge("save_assistant_message", END)

        return workflow.compile()

    async def ainvoke(self, user_id: str, message: str, deep_think: bool = False) -> Dict[str, Any]:
        """异步执行图"""
        initial_state = ChatState(
            user_id=user_id,
            message=message,
            deep_think=deep_think
        )

        final_state = await self.graph.ainvoke(initial_state)

        return {
            "response": final_state.response,
            "extracted_features": final_state.extracted_features,
            "think_content": final_state.think_content,
            "profile_updated": final_state.profile_updated,
            "errors": final_state.errors
        }
