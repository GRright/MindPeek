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
            SELECT feature_type, feature_value, confidence, reasoning
            FROM features
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
        """, (user_id,))
        
        features = cursor.fetchall()
        conn.close()
        
        return [{
            "feature_type": f[0],
            "feature_value": f[1],
            "confidence": f[2],
            "reasoning": f[3]
        } for f in features]
    except Exception as e:
        print(f"  ❌ 同步获取特征失败：{e}")
        return []

def save_feature_sync(user_id: str, feature_type: str, feature_value: str, 
                      confidence: float, reasoning: str = None) -> bool:
    """同步保存特征"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查是否已存在
        cursor.execute("""
            SELECT id, confidence FROM features
            WHERE user_id = ? AND feature_type = ? AND feature_value = ?
        """, (user_id, feature_type, feature_value))
        
        existing = cursor.fetchone()
        
        if existing:
            # 更新置信度
            new_confidence = max(existing[1], confidence)
            cursor.execute("""
                UPDATE features
                SET confidence = ?, verification_count = COALESCE(verification_count, 0) + 1,
                    updated_at = ?
                WHERE id = ?
            """, (new_confidence, datetime.utcnow(), existing[0]))
        else:
            # 插入新特征
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
