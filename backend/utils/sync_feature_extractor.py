"""
LLM 驱动的智能特征提取模块
"""
import sqlite3
import json
import asyncio
from datetime import datetime
from backend.services.llm_provider import LLMProviderFactory
from backend.core.config import ConfigManager

DB_PATH = 'C:\\myProject\\MindPeek\\data\\permir.db'

FEATURE_TYPES = [
    "MBTI", "大五人格", "行为习惯", "兴趣爱好",
    "价值观", "潜在想法", "个人信息", "情感状态",
    "社交特点", "沟通风格", "思维模式", "工作风格"
]

LLM_EXTRACTION_PROMPT = """你是一个专业的用户画像分析助手。请分析用户对话，提取用户特征。

## 对话信息
用户消息：{message}

助手回复：{response}

## 特征类型（必须使用这些类型）
- MBTI：性格类型（如 INTJ、ENFP、ISFP 等）
- 大五人格：开放性、尽责性、外向性、宜人性、神经质（每个维度 0-100 分）
- 行为习惯：日常习惯、作息规律、生活方式
- 兴趣爱好：喜欢的活动、爱好
- 价值观：人生观、爱情观、事业观
- 潜在想法：深层需求、潜在欲望、隐藏动机
- 个人信息：职业、年龄、性别、居住地等客观信息
- 情感状态：当前情绪、情感需求
- 社交特点：社交偏好、朋友关系
- 沟通风格：表达方式、倾听习惯
- 思维模式：思考方式、决策风格
- 工作风格：工作习惯、团队协作

## 推断要求
1. 仔细分析用户消息中的直接陈述
2. 从语气、用词、表达方式推断潜在特征
3. 分析用户提到的行为习惯，推断性格特点
4. 考虑文化背景和语境（如"宅"可能表示内向或享受独处）
5. 潜在特征置信度通常低于直接特征

## 输出格式（严格 JSON）
{{
    "direct_features": [
        {{
            "feature_type": "类型",
            "feature_value": "值",
            "confidence": 0.8-1.0,
            "reasoning": "推断理由"
        }}
    ],
    "inferred_features": [
        {{
            "feature_type": "类型",
            "feature_value": "值",
            "confidence": 0.5-0.75,
            "reasoning": "推断理由"
        }}
    ],
    "personality_insights": {{
            "openness": 0-100,
            "conscientiousness": 0-100,
            "extraversion": 0-100,
            "agreeableness": 0-100,
            "neuroticism": 0-100
    }},
    "summary": "一句话总结用户画像"
}}

没有发现特征时，direct_features 和 inferred_features 返回空数组。"""


def extract_features_sync(user_id: str, message: str, response: str = "") -> bool:
    """使用 LLM 进行智能特征提取"""
    try:
        config_manager = ConfigManager()
        llm = LLMProviderFactory.get_provider("openai")

        prompt = LLM_EXTRACTION_PROMPT.format(
            message=message,
            response=response if response else "（无助手回复）"
        )

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        llm_response = loop.run_until_complete(
            llm.chat([{"role": "user", "content": prompt}])
        )

        features = []
        personality_data = {}

        try:
            start = llm_response.find('{')
            end = llm_response.rfind('}') + 1
            if start != -1 and end != 0:
                result = json.loads(llm_response[start:end])
                features = result.get('direct_features', []) + result.get('inferred_features', [])
                personality_data = result.get('personality_insights', {})
        except json.JSONDecodeError as e:
            print(f"解析 LLM 返回失败: {e}")
            return False

        if features:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR IGNORE INTO profiles (user_id, created_at, updated_at)
                VALUES (?, ?, ?)
            """, (user_id, datetime.utcnow(), datetime.utcnow()))

            for feature in features:
                feature_type = feature.get('feature_type', '')
                feature_value = feature.get('feature_value', '')
                confidence = feature.get('confidence', 0.5)
                reasoning = feature.get('reasoning', '')

                if not feature_type or not feature_value:
                    continue

                cursor.execute("""
                    SELECT id, confidence FROM features
                    WHERE user_id = ? AND feature_type = ? AND feature_value = ?
                """, (user_id, feature_type, feature_value))

                existing = cursor.fetchone()

                if existing:
                    new_confidence = max(existing[1], confidence)
                    cursor.execute("""
                        UPDATE features
                        SET confidence = ?, verification_count = COALESCE(verification_count, 0) + 1,
                            updated_at = ?, reasoning = ?
                        WHERE id = ?
                    """, (new_confidence, datetime.utcnow(), reasoning, existing[0]))
                else:
                    cursor.execute("""
                        INSERT INTO features (user_id, feature_type, feature_value, confidence,
                                             reasoning, is_active, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                    """, (user_id, feature_type, feature_value, confidence, reasoning,
                          datetime.utcnow(), datetime.utcnow()))

            conn.commit()
            conn.close()

            print(f"  ✅ LLM 提取特征成功：{len(features)} 个")
            return True
        else:
            print(f"  ⚠️ LLM 未提取到特征")
            return False

    except Exception as e:
        print(f"  ❌ LLM 特征提取失败: {e}")
        import traceback
        traceback.print_exc()
        return False
