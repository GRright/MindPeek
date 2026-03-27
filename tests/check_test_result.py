"""
检查测试结果 - 直接从数据库读取特征
"""

import asyncio
import aiohttp
import json

async def check_result(user_id: str):
    """检查结果"""
    async with aiohttp.ClientSession() as session:
        # 1. 尝试获取用户画像
        print("="*60)
        print("1. 获取用户画像...")
        print("="*60)
        
        url = f"http://localhost:8000/api/profile/{user_id}"
        async with session.get(url) as response:
            if response.status == 200:
                profile = await response.json()
                print(json.dumps(profile, ensure_ascii=False, indent=2))
            else:
                print(f"获取用户画像失败：{response.status}")
        
        print("\n")
        
        # 2. 获取知识图谱数据
        print("="*60)
        print("2. 获取知识图谱数据...")
        print("="*60)
        
        kg_url = f"http://localhost:8000/api/knowledge-graph/{user_id}"
        async with session.get(kg_url) as response:
            if response.status == 200:
                kg_data = await response.json()
                print(f"节点数：{len(kg_data.get('nodes', []))}")
                print(f"边数：{len(kg_data.get('edges', []))}")
                print(f"特征类型：{kg_data.get('featureTypes', [])}")
                print("\n节点列表:")
                for node in kg_data.get('nodes', [])[:20]:  # 显示前 20 个
                    print(f"  - {node.get('label', 'N/A')} ({node.get('type', 'N/A')})")
            else:
                print(f"获取知识图谱失败：{response.status}")
        
        print("\n")
        
        # 3. 获取对话历史
        print("="*60)
        print("3. 获取对话历史...")
        print("="*60)
        
        conv_url = f"http://localhost:8000/api/profile/{user_id}/conversations?limit=10"
        async with session.get(conv_url) as response:
            if response.status == 200:
                conversations = await response.json()
                print(f"对话数量：{len(conversations)}")
                print("\n最近 10 条对话:")
                for i, conv in enumerate(conversations[-10:], 1):
                    content = conv.get('content', '')[:50]
                    print(f"  {i}. [{conv.get('role', 'N/A')}] {content}...")
            else:
                print(f"获取对话历史失败：{response.status}")

if __name__ == "__main__":
    user_id = "test_otaku_user"
    print(f"检查用户 {user_id} 的测试结果...\n")
    asyncio.run(check_result(user_id))
