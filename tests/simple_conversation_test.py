"""
简单测试 - 真正与模型对话并保存数据
"""

import asyncio
import aiohttp
import json

async def simple_test():
    """简单测试：发送 10 条消息，确保保存到数据库"""
    user_id = "test_simple_user"
    
    # 10 条典型的宅男对话
    messages = [
        "你好，我叫小明，是个程序员",
        "我平时比较宅，喜欢看看书和动漫",
        "最近在看《三体》，刘慈欣的想象力太强了",
        "周末一般就宅在家里看动漫，一看看一整天",
        "我住在上海，这里的生活节奏挺快的",
        "朋友不多，就几个，但关系都很好",
        "我一般凌晨 2 点左右睡觉，白天起不来",
        "吃饭基本都是外卖，自己不会做饭也不想学",
        "不太喜欢运动，感觉挺无聊的",
        "远程办公挺好的，不用和人打交道，效率也高"
    ]
    
    async with aiohttp.ClientSession() as session:
        print("="*60)
        print("开始简单对话测试")
        print("="*60)
        
        for i, message in enumerate(messages, 1):
            print(f"\n[{i}/10] 发送：{message}")
            
            payload = {
                "user_id": user_id,
                "message": message,
                "extract_features": True,
                "deep_think": False
            }
            
            try:
                async with session.post("http://localhost:8000/api/stream", json=payload) as response:
                    if response.status == 200:
                        # 读取完整响应
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if line.startswith('data: '):
                                data = json.loads(line[6:])
                                if data.get('type') == 'done':
                                    print(f"     回复：{data.get('content', '')[:50]}...")
                                    break
                    else:
                        print(f"     错误：{response.status}")
                        
            except Exception as e:
                print(f"     异常：{e}")
            
            # 等待 1 秒，避免请求过快
            await asyncio.sleep(1)
        
        print("\n" + "="*60)
        print("对话完成，等待特征提取...")
        print("="*60)
        
        # 等待特征提取
        await asyncio.sleep(5)
        
        # 获取用户画像
        print("\n获取用户画像...")
        async with session.get(f"http://localhost:8000/api/profile/{user_id}") as response:
            if response.status == 200:
                profile = await response.json()
                print("\n" + "="*60)
                print("用户画像结果:")
                print("="*60)
                print(f"用户 ID: {profile.get('user_id')}")
                print(f"特征数量：{len(profile.get('features', []))}")
                print(f"对话数量：{profile.get('summary', {}).get('conversation_count', 0)}")
                
                # 显示特征
                features = profile.get('features', [])
                if features:
                    print("\n特征列表:")
                    for f in features:
                        print(f"  - [{f.get('feature_type')}] {f.get('feature_value')} (置信度：{f.get('confidence', 0):.2f})")
                else:
                    print("\n⚠️  没有提取到任何特征！")
                
                print("="*60)
            else:
                print(f"获取用户画像失败：{response.status}")
        
        # 获取知识图谱
        print("\n获取知识图谱...")
        async with session.get(f"http://localhost:8000/api/knowledge-graph/{user_id}") as response:
            if response.status == 200:
                kg = await response.json()
                print(f"节点数：{len(kg.get('nodes', []))}")
                print(f"边数：{len(kg.get('edges', []))}")
                print(f"特征类型：{kg.get('featureTypes', [])}")
            else:
                print(f"获取知识图谱失败：{response.status}")

if __name__ == "__main__":
    print("简单对话测试 - 确保真正调用 API 并保存数据\n")
    asyncio.run(simple_test())
