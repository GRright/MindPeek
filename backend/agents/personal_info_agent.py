"""
PersonalInfoAgent - 从对话中提取用户个人信息和关系信息
包括：姓名、年龄、职业、个人情况、与他人/事物的关系等
"""
import json
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from ..services.llm_provider import BaseLLMProvider


class PersonalInfoExtraction(BaseModel):
    """个人信息提取结果"""
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    marital_status: Optional[str] = None
    other_info: List[Dict[str, Any]] = []


class RelationshipExtraction(BaseModel):
    """关系信息提取结果"""
    relationships: List[Dict[str, Any]] = []


class PersonalInfoAgent:
    """个人信息和关系提取 Agent"""

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def _build_personal_info_prompt(self, conversation_history: List[Dict[str, str]], message: str) -> str:
        """构建个人信息提取提示词"""
        history_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
            for m in conversation_history[-10:]
        ])

        return f"""你是一个专业的个人信息提取专家。请分析以下对话，提取用户的个人信息。

## 对话历史
{history_text}

## 用户最新消息
{message}

## 提取要求
1. 提取用户的姓名（如果对话中透露）
2. 提取年龄、性别、职业、居住地、教育背景、婚姻状况等
3. 提取其他重要的个人信息（如爱好、习惯、经历等）
4. 只提取对话中明确提到的信息，不要推测

## 输出格式（JSON）
```json
{{
    "name": "用户姓名或 null",
    "age": 年龄数字或 null,
    "gender": "性别或 null",
    "occupation": "职业或 null",
    "location": "居住地或 null",
    "education": "教育背景或 null",
    "marital_status": "婚姻状况或 null",
    "other_info": [
        {{
            "type": "信息类型",
            "value": "具体信息",
            "confidence": 0.0-1.0
        }}
    ]
}}
```

请直接返回 JSON，不要有其他内容。"""

    def _build_relationship_prompt(self, conversation_history: List[Dict[str, str]], message: str) -> str:
        """构建关系信息提取提示词"""
        history_text = "\n".join([
            f"{'用户' if m['role'] == 'user' else '助手'}: {m['content']}"
            for m in conversation_history[-10:]
        ])

        return f"""你是一个专业的关系信息提取专家。请分析以下对话，提取用户与他人或事物的关系信息。

## 对话历史
{history_text}

## 用户最新消息
{message}

## 提取要求
1. 识别对话中提到的人物（家人、朋友、同事、恋人等）
2. 识别用户与这些人物的关系类型
3. 提取关系描述（如互动模式、关系状态等）
4. 也可以提取用户与事物/组织的关系（如公司、学校、宠物等）
5. 只提取对话中明确提到的信息，不要推测

## 输出格式（JSON）
```json
{{
    "relationships": [
        {{
            "person_name": "人物姓名或称呼",
            "relationship_type": "关系类型（如：家人/朋友/同事/恋人/其他）",
            "description": "关系描述",
            "confidence": 0.0-1.0
        }}
    ]
}}
```

请直接返回 JSON，不要有其他内容。"""

    async def extract_personal_info(self, conversation_history: List[Dict[str, str]], message: str) -> PersonalInfoExtraction:
        """提取个人信息"""
        try:
            prompt = self._build_personal_info_prompt(conversation_history, message)
            response = await self.llm.chat(prompt)

            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    result = json.loads(response[start:end])
                    return PersonalInfoExtraction(**result)
            except (json.JSONDecodeError, Exception) as e:
                print(f"解析个人信息失败：{e}")

        except Exception as e:
            print(f"提取个人信息失败：{e}")

        return PersonalInfoExtraction()

    async def extract_relationships(self, conversation_history: List[Dict[str, str]], message: str) -> RelationshipExtraction:
        """提取关系信息"""
        try:
            prompt = self._build_relationship_prompt(conversation_history, message)
            response = await self.llm.chat(prompt)

            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start != -1 and end != 0:
                    result = json.loads(response[start:end])
                    return RelationshipExtraction(**result)
            except (json.JSONDecodeError, Exception) as e:
                print(f"解析关系信息失败：{e}")

        except Exception as e:
            print(f"提取关系信息失败：{e}")

        return RelationshipExtraction()

    async def extract_all(self, conversation_history: List[Dict[str, str]], message: str) -> Dict[str, Any]:
        """同时提取个人信息和关系信息"""
        personal_info, relationships = await asyncio.gather(
            self.extract_personal_info(conversation_history, message),
            self.extract_relationships(conversation_history, message)
        )

        return {
            "personal_info": personal_info.dict(),
            "relationships": relationships.dict()
        }


import asyncio

personal_info_agent = None


def get_personal_info_agent(llm_provider: BaseLLMProvider = None) -> PersonalInfoAgent:
    """获取个人信息提取 Agent 实例"""
    global personal_info_agent
    if personal_info_agent is None:
        if llm_provider is None:
            raise ValueError("LLM Provider 必须提供")
        personal_info_agent = PersonalInfoAgent(llm_provider)
    return personal_info_agent
