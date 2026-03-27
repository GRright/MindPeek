"""
直接检查数据库中的数据
"""

import sqlite3
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('C:\\myProject\\MindPeek\\data\\permir.db')
cursor = conn.cursor()

print("="*70)
print("检查数据库中的数据")
print("="*70)

# 检查用户
print("\n1. 用户列表:")
cursor.execute("SELECT user_id, created_at FROM profiles ORDER BY created_at DESC LIMIT 5")
users = cursor.fetchall()
for user in users:
    print(f"   - {user[0]} (创建时间：{user[1]})")

# 检查对话
print("\n2. 最近对话 (interactive_test_user):")
cursor.execute("""
    SELECT role, content, timestamp 
    FROM conversations 
    WHERE user_id = 'interactive_test_user' 
    ORDER BY timestamp DESC 
    LIMIT 10
""")
conversations = cursor.fetchall()
for conv in conversations:
    timestamp = conv[2][:19] if conv[2] else 'N/A'
    content = conv[1][:50] if conv[1] else 'N/A'
    print(f"   [{conv[0]}] {timestamp}: {content}...")

# 检查特征
print("\n3. 特征 (interactive_test_user):")
cursor.execute("""
    SELECT feature_type, feature_value, confidence, created_at 
    FROM features 
    WHERE user_id = 'interactive_test_user' 
    ORDER BY created_at DESC
""")
features = cursor.fetchall()
if features:
    for f in features:
        created = f[3][:19] if f[3] else 'N/A'
        print(f"   - [{f[0]}] {f[1]} (置信度：{f[2]}) {created}")
else:
    print("   没有特征！")

# 统计
print("\n4. 统计:")
cursor.execute("SELECT COUNT(*) FROM profiles")
print(f"   - 用户总数：{cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = 'interactive_test_user'")
print(f"   - interactive_test_user 对话数：{cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM features WHERE user_id = 'interactive_test_user'")
print(f"   - interactive_test_user 特征数：{cursor.fetchone()[0]}")

conn.close()

print("\n" + "="*70)
