"""
查看测试用户的知识图谱数据
"""

import asyncio
import aiohttp
import json

async def view_knowledge_graph():
    user_id = "minimal_test_user"
    
    async with aiohttp.ClientSession() as session:
        print("="*60)
        print(f"查看用户 {user_id} 的知识图谱")
        print("="*60)
        
        # 获取知识图谱
        async with session.get(f"http://localhost:8000/api/knowledge-graph/{user_id}") as response:
            if response.status == 200:
                kg = await response.json()
                print(f"\n节点数：{len(kg.get('nodes', []))}")
                print(f"边数：{len(kg.get('edges', []))}")
                print(f"特征类型：{kg.get('featureTypes', [])}")
                
                print("\n节点列表:")
                for node in kg.get('nodes', []):
                    print(f"  - ID:{node['id']} 类型:{node['type']} 名称:{node['label']}")
                
                print("\n边列表:")
                for edge in kg.get('edges', []):
                    inferred = "推断" if edge.get('inferred') else "直接"
                    print(f"  - {edge['source']} -> {edge['target']} ({edge['relation']}) [{inferred}]")
            else:
                print(f"获取知识图谱失败：{response.status}")
        
        print("\n" + "="*60)
        print("现在可以访问前端查看知识图谱可视化效果")
        print("URL: http://localhost:3000/knowledge-graph")
        print("用户 ID: minimal_test_user")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(view_knowledge_graph())
