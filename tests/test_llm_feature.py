"""测试 LLM 特征提取"""
import sys
sys.path.insert(0, 'C:\\myProject\\MindPeek')

from backend.utils.sync_feature_extractor import extract_features_sync

print("测试 LLM 特征提取...")
result = extract_features_sync(
    "test_llm_user",
    "你好，我叫小明，是个程序员，平时比较宅，喜欢看书和动漫",
    "你好！很高兴见到你，有什么我可以帮助你的吗？"
)
print(f"结果: {result}")

# 检查数据库
import sqlite3
conn = sqlite3.connect('C:\\myProject\\MindPeek\\data\\permir.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM features WHERE user_id = ?", ("test_llm_user",))
count = cursor.fetchone()[0]
print(f"特征数量: {count}")

if count > 0:
    cursor.execute("SELECT feature_type, feature_value FROM features WHERE user_id = ?", ("test_llm_user",))
    for row in cursor.fetchall():
        print(f"  - [{row[0]}] {row[1]}")

conn.close()
