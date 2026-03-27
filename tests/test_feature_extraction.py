"""测试特征提取功能"""
import requests
import json
import time

url = "http://localhost:8000/api/stream"
payload = {
    "user_id": "feature_test_user",
    "message": "你好，我叫小明，是个程序员，平时比较宅，喜欢看书和动漫",
    "extract_features": True,
    "deep_think": False
}

print("发送测试请求（启用特征提取）...")
response = requests.post(url, json=payload, stream=True)

full_response = ""
for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])
            if data.get('type') in ['done', 'error']:
                print(f"\n收到：{data.get('type')} - {str(data.get('content', ''))[:100]}")
                break

print("\n等待 3 秒让特征提取完成...")
time.sleep(3)

print("\n检查数据库...")
import sqlite3
conn = sqlite3.connect('C:\\myProject\\MindPeek\\data\\permir.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", ("feature_test_user",))
conv_count = cursor.fetchone()[0]
print(f"对话数量：{conv_count}")

cursor.execute("SELECT COUNT(*) FROM features WHERE user_id = ?", ("feature_test_user",))
feature_count = cursor.fetchone()[0]
print(f"特征数量：{feature_count}")

if feature_count > 0:
    cursor.execute("SELECT feature_type, feature_value, confidence FROM features WHERE user_id = ?", ("feature_test_user",))
    print(f"\n特征列表:")
    for row in cursor.fetchall():
        print(f"  - [{row[0]}] {row[1]} (置信度：{row[2]:.2f})")
else:
    print("\n⚠️ 没有提取到特征！")

conn.close()
