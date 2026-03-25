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
from .personal_info_agent import get_personal_info_agent, PersonalInfoAgent


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
        self.personal_info_agent = get_personal_info_agent(llm_provider)
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
            from ..models.schemas import MessageCreate, MessageRole
            await self.profile_service.add_conversation(
                state.user_id,
                MessageCreate(role=MessageRole.USER, content=state.message)
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

            try:
                response = await self.llm.chat(messages)
                state.response = response
                
                # 从 response 中提取 think_content
                if '<think>' in response and '</think>' in response:
                    import re
                    think_match = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
                    if think_match:
                        state.think_content = think_match.group(1).strip()
                        # 从 response 中移除 think 标签
                        state.response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
            except Exception as llm_error:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"LLM 调用失败：{str(llm_error)}")
                state.errors.append(f"LLM 调用失败：{str(llm_error)}, 使用模拟回复")
                state.response = f"你好！我收到了你的消息：'{state.message}'。这是一个模拟回复，因为当前没有配置有效的 LLM API 密钥。"

        except Exception as e:
            state.errors.append(f"生成回复失败: {str(e)}")
            state.response = f"抱歉，生成回复时出现错误: {str(e)}"

        return state

    async def generate_general_response(self, state: ChatState) -> ChatState:
        """生成通用回复（不使用个性化）"""
        state.use_personalization = False
        return await self.generate_personalized_response(state)

    async def extract_features(self, state: ChatState) -> ChatState:
        """使用 FeatureDiscovery Agent 和个人信息 Agent 提取用户特征"""
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

            extracted_features = []

            # 1. 使用 FeatureDiscovery Agent 提取一般特征
            try:
                discovery_result = await self.feature_discovery_agent.discover(
                    user_id=state.user_id,
                    message=state.message,
                    conversation_history=state.conversation_history,
                    existing_features=existing_features_data
                )
                extracted_features.extend(discovery_result.get("discovered_features", []))
            except Exception as fe_error:
                state.errors.append(f"FeatureDiscovery 调用失败: {str(fe_error)}, 使用模拟特征")
                extracted_features = [
                    {
                        "feature_type": "行为习惯",
                        "feature_value": "喜欢阅读",
                        "confidence": 0.8,
                        "reasoning": "用户提到喜欢周末看书"
                    }
                ]

            # 2. 使用 PersonalInfo Agent 提取个人信息和关系
            try:
                personal_info_result = await self.personal_info_agent.extract_all(
                    conversation_history=state.conversation_history,
                    message=state.message
                )

                # 提取个人信息
                personal_info = personal_info_result.get("personal_info", {})
                if personal_info.get("name"):
                    extracted_features.append({
                        "feature_type": "个人信息",
                        "feature_value": f"姓名：{personal_info['name']}",
                        "confidence": 0.9,
                        "reasoning": "用户在对话中透露了自己的姓名",
                        "evidence": [state.message]
                    })

                if personal_info.get("occupation"):
                    extracted_features.append({
                        "feature_type": "个人信息",
                        "feature_value": f"职业：{personal_info['occupation']}",
                        "confidence": 0.85,
                        "reasoning": "用户在对话中透露了自己的职业",
                        "evidence": [state.message]
                    })

                if personal_info.get("location"):
                    extracted_features.append({
                        "feature_type": "个人信息",
                        "feature_value": f"居住地：{personal_info['location']}",
                        "confidence": 0.85,
                        "reasoning": "用户在对话中透露了自己的居住地",
                        "evidence": [state.message]
                    })

                for other_info in personal_info.get("other_info", []):
                    if other_info.get("confidence", 0) >= 0.7:
                        extracted_features.append({
                            "feature_type": "个人信息",
                            "feature_value": f"{other_info.get('type', '其他')}: {other_info.get('value', '')}",
                            "confidence": other_info.get("confidence", 0.7),
                            "reasoning": "用户在对话中透露的个人信息",
                            "evidence": [state.message]
                        })

                # 提取关系信息
                relationships = personal_info_result.get("relationships", {}).get("relationships", [])
                for rel in relationships:
                    if rel.get("confidence", 0) >= 0.7:
                        await self.profile_service.add_relationship(
                            user_id=state.user_id,
                            person_name=rel.get("person_name", ""),
                            relationship_type=rel.get("relationship_type", "其他"),
                            interaction_pattern=rel.get("description"),
                            confidence=rel.get("confidence", 0.7),
                            evidence=[state.message]
                        )

            except Exception as pi_error:
                state.errors.append(f"个人信息提取失败: {str(pi_error)}")

            state.extracted_features = extracted_features

            # 3. 保存所有提取的特征到数据库
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
            from ..models.schemas import MessageCreate, MessageRole
            await self.profile_service.add_conversation(
                state.user_id,
                MessageCreate(role=MessageRole.ASSISTANT, content=state.response)
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
        """异步执行图 - 完整版本（包含特征提取和画像更新）"""
        initial_state = ChatState(
            user_id=user_id,
            message=message,
            deep_think=deep_think
        )

        final_state = await self.graph.ainvoke(initial_state)

        response = final_state.get("response", "") if isinstance(final_state, dict) else getattr(final_state, "response", "")
        extracted_features = final_state.get("extracted_features", []) if isinstance(final_state, dict) else getattr(final_state, "extracted_features", [])
        think_content = final_state.get("think_content") if isinstance(final_state, dict) else getattr(final_state, "think_content", None)
        profile_updated = final_state.get("profile_updated", False) if isinstance(final_state, dict) else getattr(final_state, "profile_updated", False)

        return {
            "response": response,
            "extracted_features": extracted_features,
            "think_content": think_content,
            "profile_updated": profile_updated
        }

    async def ainvoke_fast(self, user_id: str, message: str, deep_think: bool = False) -> Dict[str, Any]:
        """异步执行图 - 快速版本（仅获取 LLM 响应，特征提取在后台进行）"""
        initial_state = ChatState(
            user_id=user_id,
            message=message,
            deep_think=deep_think
        )

        # 快速路径：只执行到生成回复，不等待特征保存和画像更新
        final_state = await self.graph.ainvoke(initial_state)

        response = final_state.get("response", "") if isinstance(final_state, dict) else getattr(final_state, "response", "")
        extracted_features = final_state.get("extracted_features", []) if isinstance(final_state, dict) else getattr(final_state, "extracted_features", [])
        think_content = final_state.get("think_content") if isinstance(final_state, dict) else getattr(final_state, "think_content", None)
        conversation_history = final_state.get("conversation_history", []) if isinstance(final_state, dict) else getattr(final_state, "conversation_history", [])

        return {
            "response": response,
            "extracted_features": extracted_features,
            "think_content": think_content,
            "conversation_history": conversation_history,
            "profile_updated": False
        }

    async def generate_stream(self, user_id: str, message: str, deep_think: bool = False):
        """流式生成回复"""
        import re

        initial_state = ChatState(
            user_id=user_id,
            message=message,
            deep_think=deep_think
        )

        # 构建提示词
        system_prompt = self._build_personalization_prompt(initial_state)
        messages = [{"role": "system", "content": system_prompt}]

        # 加载对话历史
        try:
            conversations = await self.profile_service.get_conversation_history(user_id, limit=10)
            conversation_history = [
                {"role": c.role, "content": c.content}
                for c in conversations[-6:]
            ]
            messages.extend(conversation_history)
        except:
            pass

        messages.append({"role": "user", "content": message})

        # 流式调用 LLM
        think_content = None
        async for chunk in self.llm.chat_stream(messages):
            # 检查是否包含 think 标签
            if '<think>' in chunk and '</think>' in chunk:
                # 提取 think 内容
                think_match = re.search(r'<think>(.*?)</think>', chunk, re.DOTALL)
                if think_match:
                    think_content = think_match.group(1).strip()
                    # 移除 think 标签，只返回实际内容
                    chunk = re.sub(r'<think>.*?</think>', '', chunk, flags=re.DOTALL)

            if chunk:
                yield chunk, think_content

        # 最后一个 chunk 之后，发送最终的 think_content
        if think_content:
            yield "", think_content
