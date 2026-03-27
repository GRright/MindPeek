import requests

print("测试 /api/profile/{user_id} 端点...")
resp = requests.get('http://localhost:8000/api/profile/interactive_test_user')
print(f'Status: {resp.status_code}')

if resp.status_code == 200:
    data = resp.json()
    print(f'\n响应数据：')
    print(f'  - user_id: {data.get("user_id")}')
    print(f'  - features 数量: {len(data.get("features", []))}')
    print(f'  - summary: {data.get("summary")}')
    print(f'  - features_by_type: {data.get("features_by_type")}')
else:
    print(f'Error: {resp.text}')
