"""
同步保存对话和特征的模块
"""

import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
import json

DB_PATH = 'C:\\myProject\\MindPeek\\data\\permir.db'

def save_conversation_sync(user_id: str, role: str, content: str, session_id: str = "default") -> bool:
    """同步保存对话"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 确保用户存在
        cursor.execute("""
            INSERT OR IGNORE INTO profiles (user_id, created_at, updated_at)
            VALUES (?, ?, ?)
        """, (user_id, datetime.utcnow(), datetime.utcnow()))
        
        # 保存对话
        cursor.execute("""
            INSERT INTO conversations (user_id, role, content, session_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, role, content, session_id, datetime.utcnow()))
        
        conn.commit()
        conn.close()
        print(f"  ✅ 同步保存对话成功：{user_id} - {role}")
        return True
    except Exception as e:
        print(f"  ❌ 同步保存对话失败：{e}")
        return False

def get_user_features_sync(user_id: str) -> list:
    """同步获取用户特征"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, feature_type, feature_value, confidence, source_message, reasoning,
                   created_at, updated_at, is_active, verification_count, last_verified_at
            FROM features
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        """, (user_id,))
        
        features = cursor.fetchall()
        conn.close()
        
        return [{
            "id": f[0],
            "feature_type": f[1],
            "feature_value": f[2],
            "confidence": f[3],
            "source_message": f[4],
            "reasoning": f[5],
            "created_at": f[6],
            "updated_at": f[7],
            "is_active": f[8],
            "verification_count": f[9],
            "last_verified_at": f[10]
        } for f in features]
    except Exception as e:
        print(f"  ❌ 同步获取特征失败：{e}")
        return []

SINGLE_VALUE_TYPES = ["MBTI", "大五人格", "个人信息"]


def normalize_mbti(value: str) -> str:
    """标准化MBTI值"""
    import re
    mbti_pattern = r'[IE][NS][FT][JP]'
    match = re.search(mbti_pattern, value.upper())
    if match:
        return match.group()
    return value


def is_conflicting_value(existing_value: str, new_value: str, feature_type: str) -> bool:
    """判断两个特征值是否冲突"""
    if feature_type == "MBTI":
        existing_normalized = normalize_mbti(existing_value)
        new_normalized = normalize_mbti(new_value)
        return existing_normalized != new_normalized
    
    return existing_value != new_value


def resolve_conflict(existing_conf: float, new_conf: float, 
                     existing_value: str, new_value: str, feature_type: str) -> dict:
    """解决特征冲突，返回应该保留的特征"""
    if feature_type == "MBTI":
        existing_normalized = normalize_mbti(existing_value)
        new_normalized = normalize_mbti(new_value)
        
        if existing_normalized == new_normalized:
            return {
                "action": "update",
                "value": existing_value,
                "confidence": max(existing_conf, new_conf)
            }
        
        if new_conf > existing_conf + 0.15:
            return {
                "action": "replace",
                "value": new_value,
                "confidence": new_conf
            }
        elif existing_conf > new_conf + 0.15:
            return {
                "action": "keep",
                "value": existing_value,
                "confidence": existing_conf
            }
        else:
            return {
                "action": "update",
                "value": existing_value,
                "confidence": (existing_conf + new_conf) / 2
            }
    
    if new_conf > existing_conf + 0.1:
        return {
            "action": "replace",
            "value": new_value,
            "confidence": new_conf
        }
    
    return {
        "action": "keep",
        "value": existing_value,
        "confidence": existing_conf
    }


def save_feature_sync(user_id: str, feature_type: str, feature_value: str, 
                      confidence: float, reasoning: str = None) -> bool:
    """同步保存特征（支持冲突解决）"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if feature_type in SINGLE_VALUE_TYPES:
            cursor.execute("""
                SELECT id, feature_value, confidence FROM features
                WHERE user_id = ? AND feature_type = ? AND is_active = 1
            """, (user_id, feature_type))
            
            existing_list = cursor.fetchall()
            
            if existing_list:
                for existing in existing_list:
                    existing_id, existing_value, existing_conf = existing
                    
                    if is_conflicting_value(existing_value, feature_value, feature_type):
                        resolution = resolve_conflict(
                            existing_conf, confidence, 
                            existing_value, feature_value, feature_type
                        )
                        
                        if resolution["action"] == "replace":
                            cursor.execute("""
                                UPDATE features
                                SET feature_value = ?, confidence = ?, 
                                    verification_count = COALESCE(verification_count, 0) + 1,
                                    updated_at = ?, reasoning = ?
                                WHERE id = ?
                            """, (resolution["value"], resolution["confidence"], 
                                  datetime.utcnow(), reasoning, existing_id))
                            print(f"  🔄 特征冲突解决: {feature_type} 从 '{existing_value}' 更新为 '{resolution['value']}'")
                        elif resolution["action"] == "update":
                            cursor.execute("""
                                UPDATE features
                                SET confidence = ?, 
                                    verification_count = COALESCE(verification_count, 0) + 1,
                                    updated_at = ?
                                WHERE id = ?
                            """, (resolution["confidence"], datetime.utcnow(), existing_id))
                    else:
                        new_confidence = max(existing_conf, confidence)
                        cursor.execute("""
                            UPDATE features
                            SET confidence = ?, verification_count = COALESCE(verification_count, 0) + 1,
                                updated_at = ?, reasoning = ?
                            WHERE id = ?
                        """, (new_confidence, datetime.utcnow(), reasoning, existing_id))
                
                conn.commit()
                conn.close()
                print(f"  ✅ 同步保存特征成功：{user_id} - {feature_type}: {feature_value}")
                return True
        
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
                    updated_at = ?
                WHERE id = ?
            """, (new_confidence, datetime.utcnow(), existing[0]))
        else:
            cursor.execute("""
                INSERT INTO features (user_id, feature_type, feature_value, confidence, 
                                     reasoning, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """, (user_id, feature_type, feature_value, confidence, reasoning, 
                  datetime.utcnow(), datetime.utcnow()))
        
        conn.commit()
        conn.close()
        print(f"  ✅ 同步保存特征成功：{user_id} - {feature_type}: {feature_value}")
        return True
    except Exception as e:
        print(f"  ❌ 同步保存特征失败：{e}")
        return False


def get_user_conversations_sync(user_id: str, limit: int = 20) -> list:
    """同步获取用户对话"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role, content, timestamp
            FROM conversations
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (user_id, limit))
        
        conversations = cursor.fetchall()
        conn.close()
        
        return [{
            "role": c[0],
            "content": c[1],
            "timestamp": c[2]
        } for c in conversations]
    except Exception as e:
        print(f"  ❌ 同步获取对话失败：{e}")
        return []


def get_cached_predictions_sync(user_id: str, max_age_hours: int = 24) -> dict:
    """获取缓存的预测（如果在有效期内）
    
    Returns:
        dict: {
            "predictions": list,  # 预测列表
            "feature_count": int,  # 生成预测时的特征数量
            "is_valid": bool  # 缓存是否有效（特征数量未变化）
        }
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        # 获取缓存的预测
        cursor.execute("""
            SELECT id, prediction, category, confidence, reasoning, timeframe,
                   observable_signals, created_at
            FROM user_predictions
            WHERE user_id = ? AND created_at > ?
            ORDER BY confidence DESC
            LIMIT 10
        """, (user_id, cutoff_time.isoformat()))
        
        predictions = cursor.fetchall()
        
        # 获取当前用户的特征数量
        cursor.execute("""
            SELECT COUNT(*) 
            FROM features
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        
        current_feature_count = cursor.fetchone()[0]
        
        conn.close()
        
        # 将预测转换为字典
        predictions_list = [{
            "id": p[0],
            "prediction": p[1],
            "category": p[2],
            "confidence": p[3],
            "reasoning": p[4],
            "timeframe": p[5],
            "observable_signals": json.loads(p[6]) if p[6] else [],
            "created_at": p[7],
            "feature_count_at_generation": p[8] if len(p) > 8 else 0  # 兼容旧数据
        } for p in predictions]
        
        # 检查特征数量是否发生变化
        # 如果有预测数据，使用第一条预测的特征数量作为参考
        generated_feature_count = predictions_list[0].get('feature_count_at_generation', 0) if predictions_list else 0
        
        # 如果特征数量发生变化，缓存失效
        is_feature_count_changed = (
            generated_feature_count > 0 and 
            current_feature_count != generated_feature_count
        )
        
        return {
            "predictions": predictions_list,
            "feature_count": len(predictions_list),
            "is_valid": len(predictions_list) > 0 and not is_feature_count_changed,
            "current_feature_count": current_feature_count,
            "generated_feature_count": generated_feature_count,
            "is_feature_count_changed": is_feature_count_changed
        }
    except Exception as e:
        print(f"  ❌ 获取缓存预测失败：{e}")
        return {
            "predictions": [],
            "feature_count": 0,
            "is_valid": False,
            "current_feature_count": 0
        }


def save_predictions_sync(user_id: str, predictions: list) -> bool:
    """保存预测到数据库，同时记录生成预测时的特征数量"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取当前特征数量
        cursor.execute("""
            SELECT COUNT(*) 
            FROM features
            WHERE user_id = ? AND is_active = 1
        """, (user_id,))
        feature_count = cursor.fetchone()[0]
        
        # 清除旧的预测（保留最近的）
        cursor.execute("""
            DELETE FROM user_predictions
            WHERE user_id = ? AND created_at < datetime('now', '-7 days')
        """, (user_id,))
        
        # 插入新预测，同时记录生成时的特征数量
        for pred in predictions:
            cursor.execute("""
                INSERT INTO user_predictions 
                (user_id, prediction, category, confidence, reasoning, timeframe,
                 observable_signals, created_at, updated_at, feature_count_at_generation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                pred.get('prediction', ''),
                pred.get('category', '其他'),
                pred.get('confidence', 0.5),
                pred.get('reasoning', ''),
                pred.get('timeframe', '中期'),
                json.dumps(pred.get('observable_signals', [])),
                pred.get('created_at', datetime.utcnow().isoformat()),
                datetime.utcnow().isoformat(),
                feature_count
            ))
        
        conn.commit()
        conn.close()
        print(f"  ✅ 保存预测成功：{len(predictions)} 个")
        return True
    except Exception as e:
        print(f"  ❌ 保存预测失败：{e}")
        return False


def get_user_predictions_sync(user_id: str) -> list:
    """获取用户的预测（Top 10）"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, prediction, category, confidence, reasoning, timeframe,
                   observable_signals, created_at
            FROM user_predictions
            WHERE user_id = ?
            ORDER BY confidence DESC, created_at DESC
            LIMIT 10
        """, (user_id,))
        
        predictions = cursor.fetchall()
        conn.close()
        
        return [{
            "id": p[0],
            "prediction": p[1],
            "category": p[2],
            "confidence": p[3],
            "reasoning": p[4],
            "timeframe": p[5],
            "observable_signals": json.loads(p[6]) if p[6] else [],
            "created_at": p[7]
        } for p in predictions]
    except Exception as e:
        print(f"  ❌ 获取预测失败：{e}")
        return []
