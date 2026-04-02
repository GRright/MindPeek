"""
LLM 驱动的智能特征提取模块
"""
import sqlite3
import json
import asyncio
import re
from datetime import datetime
from backend.services.llm_provider import LLMProviderFactory
from backend.core.config import ConfigManager

DB_PATH = 'C:\\myProject\\MindPeek\\data\\permir.db'

FEATURE_TYPES = [
    "MBTI", "大五人格", "行为习惯", "兴趣爱好",
    "价值观", "潜在想法", "个人信息", "情感状态",
    "社交特点", "沟通风格", "思维模式", "工作风格",
    "人际关系", "家庭关系", "社会角色"
]

SINGLE_VALUE_TYPES = ["MBTI", "大五人格", "个人信息"]

VALID_MBTI_TYPES = ["INTJ", "INTP", "ENTJ", "ENTP", "INFJ", "INFP", "ENFJ", "ENFP",
                    "ISTJ", "ISFJ", "ESTJ", "ESFJ", "ISTP", "ISFP", "ESTP", "ESFP"]

LLM_EXTRACTION_PROMPT = """你是一个专业的用户画像分析助手。请分析用户对话，提取用户特征。

## 对话信息
用户消息：{message}

助手回复：{response}

## 特征类型（必须使用这些类型）

### 个人特质类
- MBTI：性格类型。必须是以下16种之一：INTJ, INTP, ENTJ, ENTP, INFJ, INFP, ENFJ, ENFP, ISTJ, ISFJ, ESTJ, ESFJ, ISTP, ISFP, ESTP, ESFP。如果不确定具体类型，不要提取此特征。
- 大五人格：开放性、尽责性、外向性、宜人性、神经质（每个维度 0-100 分）
- 思维模式：思考方式、决策风格、问题解决方式
- 沟通风格：表达方式、倾听习惯、沟通偏好

### 社会属性类（重点关注）
- 人际关系：社交圈大小、朋友类型、社交活跃度、亲密关系状态、人际互动模式
  示例："社交圈：小型但紧密"、"朋友类型：多为同事"、"亲密关系：单身"、"人际互动：被动社交"
- 家庭关系：家庭结构、与父母关系、与配偶/伴侣关系、与子女关系、家庭氛围
  示例："家庭结构：核心家庭"、"与父母关系：疏远"、"家庭氛围：和谐"
- 社会角色：职业身份、社会地位、群体归属、角色认知
  示例："职业身份：技术骨干"、"群体归属：创业者圈子"、"角色认知：团队协作者"
- 社交特点：社交偏好、社交场合表现、社交能量来源
  示例："社交偏好：小群体深度交流"、"社交能量：内向型充电"

### 行为与兴趣类
- 行为习惯：日常习惯、作息规律、生活方式
- 兴趣爱好：喜欢的活动、爱好、娱乐偏好
- 工作风格：工作习惯、团队协作方式、职业态度

### 情感与价值观类
- 情感状态：当前情绪、情感需求、心理状态
- 价值观：人生观、爱情观、事业观、金钱观
- 潜在想法：深层需求、潜在欲望、隐藏动机

### 基础信息类
- 个人信息：职业、年龄、性别、居住地、教育背景等客观信息

## 重要规则
1. MBTI类型必须是确定的单一类型，禁止使用"或"、"可能是"、"倾向于"等模糊表达
2. 如果用户信息不足以确定具体MBTI类型，不要提取MBTI特征
3. 个人信息特征值必须具体明确，如"职业：程序员"而不是"职业：可能是程序员或设计师"
4. 每种单一值特征类型（MBTI、大五人格、个人信息）只能提取一个确定的值
5. 社会属性特征要具体，避免过于笼统的描述
6. 关注用户在对话中透露的人际关系细节，如提到家人、朋友、同事等

## 推断要求
1. 仔细分析用户消息中的直接陈述
2. 从语气、用词、表达方式推断潜在特征
3. 分析用户提到的行为习惯，推断性格特点
4. 特别关注用户提到的人际互动、家庭情况、社会角色等信息
5. 考虑文化背景和语境（如"宅"可能表示内向或享受独处）
6. 潜在特征置信度通常低于直接特征

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


def normalize_mbti(value: str) -> str:
    """标准化MBTI值"""
    mbti_pattern = r'[IE][NS][FT][JP]'
    match = re.search(mbti_pattern, value.upper())
    if match:
        return match.group()
    return value


def is_valid_mbti(value: str) -> bool:
    """检查是否是有效的MBTI类型"""
    normalized = normalize_mbti(value)
    return normalized in VALID_MBTI_TYPES


def is_ambiguous_value(value: str, feature_type: str) -> bool:
    """检查特征值是否模糊/有歧义"""
    ambiguous_patterns = [
        r'或', r'可能', r'倾向', r'也许', r'大概',
        r'或者', r'像是', r'似乎', r'好像',
        r'[？?]{2,}', r'\d+种', r'之间'
    ]
    
    for pattern in ambiguous_patterns:
        if re.search(pattern, value):
            return True
    
    if feature_type == "MBTI":
        mbti_count = len(re.findall(r'[IE][NS][FT][JP]', value.upper()))
        if mbti_count > 1:
            return True
        if mbti_count == 0:
            return True
    
    return False


def is_conflicting_value(existing_value: str, new_value: str, feature_type: str) -> bool:
    """判断两个特征值是否冲突"""
    if feature_type == "MBTI":
        existing_normalized = normalize_mbti(existing_value)
        new_normalized = normalize_mbti(new_value)
        return existing_normalized != new_normalized
    
    if feature_type in ["人际关系", "家庭关系", "社会角色"]:
        existing_key = existing_value.split("：")[0] if "：" in existing_value else existing_value
        new_key = new_value.split("：")[0] if "：" in new_value else new_value
        return existing_key == new_key and existing_value != new_value
    
    return existing_value != new_value


def resolve_conflict(existing: dict, new_feature: dict, feature_type: str) -> dict:
    """解决特征冲突，返回应该保留的特征"""
    existing_conf = existing.get("confidence", 0.5)
    new_conf = new_feature.get("confidence", 0.5)
    
    if feature_type == "MBTI":
        existing_normalized = normalize_mbti(existing.get("feature_value", ""))
        new_normalized = normalize_mbti(new_feature.get("feature_value", ""))
        
        if existing_normalized == new_normalized:
            return {
                "action": "update",
                "value": existing.get("feature_value"),
                "confidence": max(existing_conf, new_conf)
            }
        
        if new_conf > existing_conf + 0.15:
            return {
                "action": "replace",
                "value": new_feature.get("feature_value"),
                "confidence": new_conf
            }
        elif existing_conf > new_conf + 0.15:
            return {
                "action": "keep",
                "value": existing.get("feature_value"),
                "confidence": existing_conf
            }
        else:
            return {
                "action": "update",
                "value": existing.get("feature_value"),
                "confidence": (existing_conf + new_conf) / 2
            }
    
    if new_conf > existing_conf + 0.1:
        return {
            "action": "replace",
            "value": new_feature.get("feature_value"),
            "confidence": new_conf
        }
    
    return {
        "action": "keep",
        "value": existing.get("feature_value"),
        "confidence": existing_conf
    }


def validate_and_clean_feature(feature: dict) -> dict:
    """验证并清理特征值"""
    feature_type = feature.get("feature_type", "")
    feature_value = feature.get("feature_value", "")
    confidence = feature.get("confidence", 0.5)
    
    if not feature_type or not feature_value:
        return None
    
    if feature_type == "MBTI":
        if is_ambiguous_value(feature_value, feature_type):
            print(f"  ⚠️ 跳过模糊的MBTI特征: {feature_value}")
            return None
        
        if not is_valid_mbti(feature_value):
            print(f"  ⚠️ 跳过无效的MBTI特征: {feature_value}")
            return None
        
        feature_value = normalize_mbti(feature_value)
        feature["feature_value"] = feature_value
    
    if feature_type in SINGLE_VALUE_TYPES:
        if is_ambiguous_value(feature_value, feature_type):
            print(f"  ⚠️ 跳过模糊的{feature_type}特征: {feature_value}")
            return None
    
    if confidence < 0.3:
        print(f"  ⚠️ 跳过低置信度特征: {feature_type}={feature_value} ({confidence:.2f})")
        return None
    
    return feature


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
                raw_features = result.get('direct_features', []) + result.get('inferred_features', [])
                
                for f in raw_features:
                    cleaned = validate_and_clean_feature(f)
                    if cleaned:
                        features.append(cleaned)
                
                personality_data = result.get('personality_insights', {})
        except json.JSONDecodeError as e:
            print(f"解析 LLM 返回失败: {e}")
            return False

        if not features:
            print(f"  ⚠️ LLM 未提取到有效特征")
            return True

        conn = sqlite3.connect(DB_PATH)
        conn.text_factory = str
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

            if feature_type in SINGLE_VALUE_TYPES:
                cursor.execute("""
                    SELECT id, feature_value, confidence FROM features
                    WHERE user_id = ? AND feature_type = ? AND is_active = 1
                """, (user_id, feature_type))
                
                existing_list = cursor.fetchall()
                
                if existing_list:
                    for existing in existing_list:
                        existing_dict = {
                            "id": existing[0],
                            "feature_value": existing[1],
                            "confidence": existing[2]
                        }
                        
                        if is_conflicting_value(existing[1], feature_value, feature_type):
                            resolution = resolve_conflict(existing_dict, feature, feature_type)
                            
                            if resolution["action"] == "replace":
                                cursor.execute("""
                                    UPDATE features
                                    SET feature_value = ?, confidence = ?, 
                                        verification_count = COALESCE(verification_count, 0) + 1,
                                        updated_at = ?, reasoning = ?
                                    WHERE id = ?
                                """, (resolution["value"], resolution["confidence"], 
                                      datetime.utcnow(), reasoning, existing[0]))
                                print(f"  🔄 特征冲突解决: {feature_type} 从 '{existing[1]}' 更新为 '{resolution['value']}'")
                            elif resolution["action"] == "update":
                                cursor.execute("""
                                    UPDATE features
                                    SET confidence = ?, 
                                        verification_count = COALESCE(verification_count, 0) + 1,
                                        updated_at = ?
                                    WHERE id = ?
                                """, (resolution["confidence"], datetime.utcnow(), existing[0]))
                        else:
                            new_confidence = max(existing[2], confidence)
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
                    print(f"  [OK] 新特征: {feature_type} = {feature_value} ({confidence:.0%})")
            else:
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
                    print(f"  [OK] 新特征: {feature_type} = {feature_value} ({confidence:.0%})")

        conn.commit()
        conn.close()

        print(f"  [OK] LLM 提取特征成功：{len(features)} 个有效特征")
        return True

    except Exception as e:
        print(f"  [ERROR] LLM 特征提取失败: {e}")
        import traceback
        traceback.print_exc()
        return False
