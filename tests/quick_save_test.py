"""快速测试后端保存对话功能"""
import requests
import json

url = "http://localhost:8000/api/stream"
payload = {
    "user_id": "quick_test",
    "message": "你好，我是测试用户",
    "extract_features": False,
    "deep_think": False
}

print("发送测试请求...")
response = requests.post(url, json=payload, stream=True)

full_response = ""
for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])
            print(f"收到：{data.get('type')} - {str(data.get('content', ''))[:100]}")
            if data.get('type') == 'done':
                break

print("\n检查数据库...")
import sys
sys.path.insert(0, 'C:\\myProject\\MindPeek')
import sqlite3

conn = sqlite3.connect('C:\\myProject\\MindPeek\\data\\permir.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = ?", ("quick_test",))
count = cursor.fetchone()[0]
print(f"quick_test 的对话数量：{count}")

if count > 0:
    cursor.execute("SELECT role, content FROM conversations WHERE user_id = ? LIMIT 5", ("quick_test",))
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1][:50]}")
else:
    print("  ❌ 对话没有被保存！")

conn.close()
