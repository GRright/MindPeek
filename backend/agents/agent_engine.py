"""
多Agent分析引擎 - 协作式特征提取
"""
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from ..services.llm_provider import LLMProviderFactory, BaseLLMProvider
from ..knowledge_graph.hybrid_graph import knowledge_graph


@dataclass
class AgentResult:
    agent_name: str
    task_type: str
    result: Dict[str, Any]
    confidence: float
    reasoning: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, name: str, llm_provider: BaseLLMProvider):
        self.name = name
        self.llm = llm_provider
    
    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> AgentResult:
        """执行分析任务"""
        pass
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """构建提示词"""
        raise NotImplementedError


class MBTIAgent(BaseAgent):
    """MBTI性格分析Agent"""
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResult:
        prompt = self._build_prompt(context)
        
        try:
            response = await self.llm.chat([{"role": "user", "content": prompt}])
            result = self._parse_response(response)
            
            return AgentResult(
                agent_name=self.name,
                task_type="mbti_analysis",
                result=result,
                confidence=result.get("confidence", 0.7),
                reasoning=result.get("reasoning", "")
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                task_type="mbti_analysis",
                result={},
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}"
            )
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        messages = context.get("messages", [])
        existing_features = context.get("existing_features", {})
        
        history_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
            for m in messages[-10:]
        ])
        
        existing_mbti = existing_features.get("MBTI", [])
        existing_text = "\n".join([f"- {f}" for f in existing_mbti]) if existing_mbti else "暂无"
        
        return f"""你是一个专业的MBTI性格分析师。请分析以下对话，推断用户的MBTI性格类型。

## MBTI四个维度
1. E/I（外向/内向）：能量来源是外部世界还是内心世界
2. S/N（感觉/直觉）：关注具体细节还是抽象概念
3. T/F（思考/情感）：决策依据是逻辑还是价值观
4. J/P（判断/感知）：生活方式是计划还是灵活

## 对话历史
{history_text}

## 已识别的MBTI特征
{existing_text}

## 分析要求
1. 基于对话内容分析每个维度的倾向
2. 给出每个维度的置信度（0-1）
3. 解释推断依据
4. 如果信息不足，标注为"待确认"

## 输出格式（JSON）
{{
    "dimensions": {{
        "EI": {{"tendency": "I/E", "confidence": 0.0-1.0, "evidence": "依据"}},
        "SN": {{"tendency": "S/N", "confidence": 0.0-1.0, "evidence": "依据"}},
        "TF": {{"tendency": "T/F", "confidence": 0.0-1.0, "evidence": "依据"}},
        "JP": {{"tendency": "J/P", "confidence": 0.0-1.0, "evidence": "依据"}}
    }},
    "mbti_type": "XXXX",
    "confidence": 0.0-1.0,
    "reasoning": "综合分析"
}}

请直接返回JSON："""
    
    def _parse_response(self, response: str) -> Dict:
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return {"confidence": 0.0, "reasoning": "解析失败"}


class BigFiveAgent(BaseAgent):
    """大五人格分析Agent"""
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResult:
        prompt = self._build_prompt(context)
        
        try:
            response = await self.llm.chat([{"role": "user", "content": prompt}])
            result = self._parse_response(response)
            
            return AgentResult(
                agent_name=self.name,
                task_type="big_five_analysis",
                result=result,
                confidence=result.get("overall_confidence", 0.7),
                reasoning=result.get("reasoning", "")
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                task_type="big_five_analysis",
                result={},
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}"
            )
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        messages = context.get("messages", [])
        
        history_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
            for m in messages[-10:]
        ])
        
        return f"""你是一个专业的大五人格分析师。请分析以下对话，评估用户的大五人格特质。

## 大五人格维度
1. 开放性：好奇心、创造力、求新求变
2. 尽责性：自律、目标导向、可靠性
3. 外向性：社交活跃、乐观、自信
4. 宜人性：信任他人、利他主义、同理心
5. 神经质：情绪波动、焦虑倾向、敏感

## 对话历史
{history_text}

## 分析要求
1. 对每个维度进行评分（0-100）
2. 给出评分依据
3. 识别最显著的特征

## 输出格式（JSON）
{{
    "traits": {{
        "开放性": {{"score": 0-100, "evidence": "依据"}},
        "尽责性": {{"score": 0-100, "evidence": "依据"}},
        "外向性": {{"score": 0-100, "evidence": "依据"}},
        "宜人性": {{"score": 0-100, "evidence": "依据"}},
        "神经质": {{"score": 0-100, "evidence": "依据"}}
    }},
    "dominant_traits": ["最显著特征1", "最显著特征2"],
    "overall_confidence": 0.0-1.0,
    "reasoning": "综合分析"
}}

请直接返回JSON："""
    
    def _parse_response(self, response: str) -> Dict:
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return {"overall_confidence": 0.0, "reasoning": "解析失败"}


class BehaviorHabitAgent(BaseAgent):
    """行为习惯分析Agent"""
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResult:
        prompt = self._build_prompt(context)
        
        try:
            response = await self.llm.chat([{"role": "user", "content": prompt}])
            result = self._parse_response(response)
            
            return AgentResult(
                agent_name=self.name,
                task_type="behavior_analysis",
                result=result,
                confidence=result.get("confidence", 0.7),
                reasoning=result.get("reasoning", "")
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                task_type="behavior_analysis",
                result={},
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}"
            )
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        messages = context.get("messages", [])
        
        history_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
            for m in messages[-10:]
        ])
        
        return f"""你是一个专业的行为习惯分析师。请分析以下对话，识别用户的行为习惯。

## 分析维度
1. 作息习惯：早起/晚睡、作息规律性
2. 消费习惯：理性/冲动、注重性价比/品质
3. 社交习惯：线上/线下、社交频率
4. 沟通风格：直接/委婉、表达方式
5. 学习/工作习惯：计划性、执行力

## 对话历史
{history_text}

## 分析要求
1. 识别用户表现出的行为习惯
2. 给出每个习惯的置信度
3. 提取支持证据

## 输出格式（JSON）
{{
    "habits": [
        {{
            "category": "作息/消费/社交/沟通/工作",
            "habit": "具体习惯描述",
            "confidence": 0.0-1.0,
            "evidence": "对话中的证据"
        }}
    ],
    "confidence": 0.0-1.0,
    "reasoning": "综合分析"
}}

请直接返回JSON："""
    
    def _parse_response(self, response: str) -> Dict:
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return {"habits": [], "confidence": 0.0, "reasoning": "解析失败"}


class ImplicitIntentAgent(BaseAgent):
    """隐性意图分析Agent"""
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResult:
        prompt = self._build_prompt(context)
        
        try:
            response = await self.llm.chat([{"role": "user", "content": prompt}])
            result = self._parse_response(response)
            
            return AgentResult(
                agent_name=self.name,
                task_type="implicit_intent_analysis",
                result=result,
                confidence=result.get("confidence", 0.7),
                reasoning=result.get("reasoning", "")
            )
        except Exception as e:
            return AgentResult(
                agent_name=self.name,
                task_type="implicit_intent_analysis",
                result={},
                confidence=0.0,
                reasoning=f"分析失败: {str(e)}"
            )
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        messages = context.get("messages", [])
        latest_message = context.get("latest_message", "")
        
        history_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
            for m in messages[-10:]
        ])
        
        return f"""你是一个专业的心理分析师，擅长识别用户的隐性意图和潜在想法。

## 分析重点
1. 未明说的需求：用户真正想要什么？
2. 潜在顾虑：用户担心什么？
3. 隐藏偏好：用户没有直接表达但暗示的偏好
4. 情感状态：用户当前的情绪和心理状态

## 对话历史
{history_text}

## 最新消息
{latest_message}

## 分析要求
1. 深入分析用户话语背后的真实意图
2. 识别可能的矛盾或隐藏信息
3. 推断用户的心理需求

## 输出格式（JSON）
{{
    "implicit_intents": [
        {{
            "type": "未明说需求/潜在顾虑/隐藏偏好/情感状态",
            "content": "具体内容",
            "confidence": 0.0-1.0,
            "evidence": "支持证据",
            "suggestion": "可能的回应建议"
        }}
    ],
    "emotional_state": {{
        "primary_emotion": "主要情绪",
        "intensity": 0.0-1.0,
        "indicators": ["情绪指标"]
    }},
    "confidence": 0.0-1.0,
    "reasoning": "综合分析"
}}

请直接返回JSON："""
    
    def _parse_response(self, response: str) -> Dict:
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return {"implicit_intents": [], "confidence": 0.0, "reasoning": "解析失败"}


class CorrelationAgent(BaseAgent):
    """特征关联分析Agent"""

    async def analyze(self, context: Dict[str, Any]) -> AgentResult:
        new_features = context.get("new_features", [])
        existing_features = context.get("existing_features", {})

        correlations = []
        all_feature_values = set()

        for feature in new_features:
            feature_value = feature.get("value", "")
            if feature_value:
                all_feature_values.add(feature_value)
                inferred = knowledge_graph._get_inferred_features(feature_value)
                for inf in inferred:
                    correlations.append({
                        "source": feature_value,
                        "target": inf,
                        "relation": "implies",
                        "weight": 0.7,
                        "inferred": True
                    })

        conflicts = []
        existing_values = []
        for features_list in existing_features.values():
            for f in features_list:
                val = f.get("value", "") if isinstance(f, dict) else f
                if val:
                    existing_values.append(val)
                    all_feature_values.add(val)

        for feature in new_features:
            feature_value = feature.get("value", "")
            if not feature_value:
                continue
            for existing_val in existing_values:
                if feature_value == existing_val:
                    continue
                inf_new = set(knowledge_graph._get_inferred_features(feature_value))
                inf_exist = set(knowledge_graph._get_inferred_features(existing_val))
                common = inf_new & inf_exist
                if common:
                    for shared in common:
                        correlations.append({
                            "source": feature_value,
                            "target": existing_val,
                            "relation": "correlates_with",
                            "weight": 0.6,
                            "inferred": True
                        })

        return AgentResult(
            agent_name=self.name,
            task_type="correlation_analysis",
            result={
                "correlations": correlations,
                "conflicts": conflicts,
                "inference_suggestions": self._generate_inference_suggestions(correlations)
            },
            confidence=0.8,
            reasoning="基于知识库的关联分析"
        )
    
    def _generate_inference_suggestions(self, correlations: List[Dict]) -> List[Dict]:
        suggestions = []
        for corr in correlations:
            if corr["relation"] == "implies" and corr["weight"] > 0.7:
                suggestions.append({
                    "inferred_feature": corr["target"],
                    "confidence": corr["weight"],
                    "based_on": corr["source"]
                })
        return suggestions


class AgentOrchestrator:
    """Agent编排器 - 协调多个Agent协作"""
    
    def __init__(self, provider_type: str = "qwen"):
        self.llm = LLMProviderFactory.get_provider(provider_type)
        
        self.agents = {
            "mbti": MBTIAgent("MBTI分析Agent", self.llm),
            "big_five": BigFiveAgent("大五人格Agent", self.llm),
            "behavior": BehaviorHabitAgent("行为习惯Agent", self.llm),
            "implicit_intent": ImplicitIntentAgent("隐性意图Agent", self.llm),
            "correlation": CorrelationAgent("关联分析Agent", self.llm)
        }
    
    async def analyze_conversation(self, messages: List[Dict], 
                                    existing_features: Dict = None,
                                    analysis_types: List[str] = None) -> Dict[str, AgentResult]:
        """执行全面分析"""
        if analysis_types is None:
            analysis_types = ["mbti", "big_five", "behavior", "implicit_intent", "correlation"]
        
        context = {
            "messages": messages,
            "latest_message": messages[-1].get("content", "") if messages else "",
            "existing_features": existing_features or {}
        }
        
        tasks = []
        for agent_type in analysis_types:
            if agent_type in self.agents:
                tasks.append(self.agents[agent_type].analyze(context))
        
        results = await asyncio.gather(*tasks)
        
        return {result.agent_name: result for result in results}
    
    async def extract_features(self, messages: List[Dict], 
                                existing_features: Dict = None) -> List[Dict]:
        """提取特征"""
        analysis_results = await self.analyze_conversation(
            messages, existing_features,
            ["mbti", "big_five", "behavior", "implicit_intent"]
        )
        
        features = []
        
        for agent_name, result in analysis_results.items():
            if result.confidence < 0.5:
                continue
            
            if agent_name == "MBTI分析Agent":
                mbti_result = result.result
                if mbti_result.get("mbti_type"):
                    features.append({
                        "type": "MBTI",
                        "value": mbti_result["mbti_type"],
                        "confidence": mbti_result.get("confidence", 0.7),
                        "reasoning": mbti_result.get("reasoning", ""),
                        "details": mbti_result.get("dimensions", {})
                    })
            
            elif agent_name == "大五人格Agent":
                big_five_result = result.result
                traits = big_five_result.get("traits", {})
                for trait_name, trait_data in traits.items():
                    features.append({
                        "type": "大五人格",
                        "value": f"{trait_name}: {trait_data.get('score', 50)}",
                        "confidence": big_five_result.get("overall_confidence", 0.7),
                        "reasoning": trait_data.get("evidence", "")
                    })
            
            elif agent_name == "行为习惯Agent":
                behavior_result = result.result
                for habit in behavior_result.get("habits", []):
                    features.append({
                        "type": "行为习惯",
                        "value": f"{habit['category']}: {habit['habit']}",
                        "confidence": habit.get("confidence", 0.7),
                        "reasoning": habit.get("evidence", "")
                    })
            
            elif agent_name == "隐性意图Agent":
                intent_result = result.result
                for intent in intent_result.get("implicit_intents", []):
                    features.append({
                        "type": "潜在想法",
                        "value": f"{intent['type']}: {intent['content']}",
                        "confidence": intent.get("confidence", 0.7),
                        "reasoning": intent.get("evidence", "")
                    })
        
        return features
    
    async def update_with_correlation(self, user_id: str, new_features: List[Dict],
                                       existing_features: Dict) -> Dict:
        """使用关联分析更新特征"""
        correlation_agent = self.agents["correlation"]
        
        result = await correlation_agent.analyze({
            "new_features": new_features,
            "existing_features": existing_features
        })
        
        correlation_data = result.result
        
        inferred_features = []
        for suggestion in correlation_data.get("inference_suggestions", []):
            inferred_features.append({
                "type": "推断特征",
                "value": suggestion["inferred_feature"],
                "confidence": suggestion["confidence"] * 0.8,
                "reasoning": f"基于 {suggestion['based_on']} 推断",
                "inferred": True
            })
        
        return {
            "inferred_features": inferred_features,
            "conflicts": correlation_data.get("conflicts", []),
            "correlations": correlation_data.get("correlations", [])
        }
