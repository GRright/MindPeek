"""
异步Agent任务编排器 - 管理后台Agent任务
支持深度思考、特征关联分析、社会关系发现等异步任务
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from ..services.llm_provider import BaseLLMProvider


class TaskType(Enum):
    DEEP_THINK = "deep_think"
    FEATURE_CORRELATION = "feature_correlation"
    RELATIONSHIP_DISCOVERY = "relationship_discovery"
    PROFILE_UPDATE = "profile_update"
    MEMORY_CONSOLIDATION = "memory_consolidation"
    LATENT_INTENT = "latent_intent"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    task_id: str
    task_type: TaskType
    user_id: str
    status: TaskStatus = TaskStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    priority: int = 0


class AsyncAgentOrchestrator:
    """异步Agent任务编排器"""

    def __init__(self, llm_provider: BaseLLMProvider, max_concurrent: int = None):
        self.llm = llm_provider
        self.tasks: Dict[str, AgentTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

        if max_concurrent is not None:
            self.max_concurrent_tasks = max_concurrent
        else:
            try:
                import json
                import os
                config_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "config", "config.json"
                )
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    self.max_concurrent_tasks = config.get("agent", {}).get("max_concurrent_agents", 3)
                else:
                    self.max_concurrent_tasks = 3
            except Exception:
                self.max_concurrent_tasks = 3

    async def submit_task(
        self,
        task_type: TaskType,
        user_id: str,
        input_data: Dict[str, Any],
        priority: int = 0
    ) -> str:
        """提交异步任务"""
        task_id = f"{task_type.value}_{user_id}_{datetime.utcnow().timestamp()}"

        task = AgentTask(
            task_id=task_id,
            task_type=task_type,
            user_id=user_id,
            input_data=input_data,
            priority=priority
        )

        self.tasks[task_id] = task

        if len(self.running_tasks) < self.max_concurrent_tasks:
            asyncio.create_task(self._run_task(task))
        else:
            await self._schedule_task(task)

        return task_id

    async def _schedule_task(self, task: AgentTask):
        """调度任务"""
        while len(self.running_tasks) >= self.max_concurrent_tasks:
            await asyncio.sleep(0.5)

        await self._run_task(task)

    async def _run_task(self, task: AgentTask):
        """运行任务"""
        task.status = TaskStatus.RUNNING
        self.running_tasks[task.task_id] = asyncio.current_task()

        try:
            if task.task_type == TaskType.DEEP_THINK:
                result = await self._deep_think_analysis(task.input_data)
            elif task.task_type == TaskType.FEATURE_CORRELATION:
                result = await self._feature_correlation_analysis(task.input_data)
            elif task.task_type == TaskType.RELATIONSHIP_DISCOVERY:
                result = await self._relationship_discovery(task.input_data)
            elif task.task_type == TaskType.MEMORY_CONSOLIDATION:
                result = await self._memory_consolidation(task.input_data)
            elif task.task_type == TaskType.LATENT_INTENT:
                result = await self._latent_intent_discovery(task.input_data)
            else:
                result = {"error": f"Unknown task type: {task.task_type}"}

            task.output_data = result
            task.status = TaskStatus.COMPLETED

        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED

        finally:
            task.completed_at = datetime.utcnow()
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]

    async def _deep_think_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """深度思考分析"""
        message = input_data.get("message", "")
        conversation_history = input_data.get("conversation_history", [])
        user_features = input_data.get("user_features", [])

        context_parts = []
        for f in user_features:
            if f.get("confidence", 0) >= 0.6:
                context_parts.append(f"- {f.get('feature_type', '未知')}: {f.get('feature_value', '')}（置信度: {f.get('confidence', 0):.0%}）")

        user_context = "\n".join(context_parts) if context_parts else ""

        system_prompt = f"""你是一个专业的心理分析师。请对用户的最新消息进行深度思考分析。

## 分析要求
1. 深入分析用户言语背后的心理状态和潜在需求
2. 识别用户的情绪变化和隐含意图
3. 推断用户可能的人格特质和价值观
4. 用简洁专业的语言输出分析结果
5. 如果用户有画像信息，结合画像进行更精准的分析{user_context}

## 输出格式
请用JSON格式输出：
{{
    "deep_analysis": "深度分析内容...",
    "emotional_state": "当前情绪状态",
    "potential_needs": ["潜在需求1", "潜在需求2"],
    "personality_insights": "人格洞察..."
}}

请直接输出JSON，不要有其他内容。"""

        messages_for_analysis = [
            {"role": c.get("role", "user"), "content": c.get("content", "")}
            for c in conversation_history[-20:]
        ]
        messages_for_analysis.append({"role": "user", "content": message})

        all_messages = [{"role": "system", "content": system_prompt}]
        all_messages.extend(messages_for_analysis)

        response = await self.llm.chat(all_messages)

        try:
            result = json.loads(response)
            return {"think_content": result, "raw_response": response}
        except json.JSONDecodeError:
            return {"think_content": {"error": "解析失败"}, "raw_response": response}

    async def _feature_correlation_analysis(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """特征关联分析"""
        new_features = input_data.get("new_features", [])
        existing_features = input_data.get("existing_features", [])

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

请直接返回JSON。"""

        messages = [
            {"role": "system", "content": "你是一个专业的特征关联分析专家。"},
            {"role": "user", "content": prompt}
        ]

        response = await self.llm.chat(messages)

        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            return {"inferred_features": [], "correlations": [], "error": "解析失败"}

        return {"inferred_features": [], "correlations": []}

    async def _relationship_discovery(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """社会关系发现"""
        message = input_data.get("message", "")
        conversation_history = input_data.get("conversation_history", [])

        history_text = "\n".join([
            f"{'用户' if m.get('role') == 'user' else '助手'}: {m.get('content', '')}"
            for m in conversation_history[-10:]
        ])

        system_prompt = f"""你是一个社会关系分析专家。请分析用户的对话，发现其中涉及的社会关系和人物互动。

## 对话历史
{history_text}

## 分析要求
1. 识别对话中提到的人物及其关系（如家人、朋友、同事、伴侣等）
2. 分析用户与这些人物之间的互动模式
3. 推断用户的社会关系特点

## 输出格式（JSON）
{{
    "relationships": [
        {{
            "person": "人物名称或描述",
            "relationship_type": "关系类型（家人/朋友/同事/伴侣等）",
            "interaction_pattern": "互动模式描述",
            "evidence": ["证据1", "证据2"],
            "confidence": 0.0-1.0
        }}
    ],
    "social_insights": "社会关系洞察..."
}}

请直接返回JSON。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]

        response = await self.llm.chat(messages)

        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            return {"relationships": [], "social_insights": "", "error": "解析失败"}

        return {"relationships": [], "social_insights": ""}

    async def _memory_consolidation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """记忆整合"""
        user_id = input_data.get("user_id", "")
        recent_features = input_data.get("recent_features", [])

        if len(recent_features) < 3:
            return {"consolidated_features": recent_features, "summary": ""}

        system_prompt = f"""你是一个记忆整合专家。请分析用户的最近对话，提取关键的长期记忆信息。

## 最近特征
{json.dumps(recent_features, ensure_ascii=False, indent=2)}

## 分析要求
1. 识别哪些是短期信息、哪些可能成为长期记忆
2. 将相关信息整合到已有的认知框架中
3. 生成简洁的记忆摘要

## 输出格式（JSON）
{{
    "consolidated_features": [
        {{
            "feature_type": "类型",
            "feature_value": "值",
            "confidence": 0.0-1.0,
            "memory_type": "short_term/long_term"
        }}
    ],
    "summary": "记忆摘要..."
}}

请直接返回JSON。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "请整合这些特征信息"}
        ]

        response = await self.llm.chat(messages)

        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            return {"consolidated_features": recent_features, "summary": "", "error": "解析失败"}

        return {"consolidated_features": recent_features, "summary": ""}

    async def _latent_intent_discovery(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """隐性需求发现"""
        from .feature_discovery import LatentIntentAgent

        latent_agent = LatentIntentAgent(self.llm)

        message = input_data.get("message", "")
        conversation_history = input_data.get("conversation_history", [])
        existing_features = input_data.get("existing_features", [])

        result = await latent_agent.discover_latent_intents(
            user_id=input_data.get("user_id", ""),
            message=message,
            conversation_history=conversation_history,
            existing_features=existing_features
        )

        return result

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "status": task.status.value,
            "output_data": task.output_data,
            "error": task.error,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }

    def get_user_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有任务"""
        return [
            self.get_task_status(task.task_id)
            for task in self.tasks.values()
            if task.user_id == user_id
        ]


global_orchestrator: Optional[AsyncAgentOrchestrator] = None


def get_orchestrator(llm_provider: BaseLLMProvider = None) -> AsyncAgentOrchestrator:
    """获取全局编排器实例"""
    global global_orchestrator
    if global_orchestrator is None and llm_provider is not None:
        global_orchestrator = AsyncAgentOrchestrator(llm_provider)
    return global_orchestrator
