"""
交互式对话测试 - 一问一答模式
模拟宅男形象与模型进行真实对话
"""

import asyncio
import aiohttp
import json

# 用户设定
USER_PROFILE = {
    "name": "小明",
    "age": 25,
    "gender": "男",
    "occupation": "程序员",
    "hobbies": ["看书", "动漫", "游戏"],
    "living_city": "上海",
}

# 对话列表（按顺序发送）
CONVERSATIONS = [
    "你好，我叫小明，是个程序员",
    "我平时比较宅，喜欢看看书和动漫",
    "最近在看《三体》，刘慈欣的想象力太强了",
    "周末一般就宅在家里看动漫，一看看一整天",
    "我住在上海，这里的生活节奏挺快的",
    "朋友不多，就几个，但关系都很好",
    "我一般凌晨 2 点左右睡觉，白天起不来",
    "吃饭基本都是外卖，自己不会做饭也不想学",
    "不太喜欢运动，感觉挺无聊的",
    "远程办公挺好的，不用和人打交道，效率也高",
    "最喜欢《进击的巨人》和《命运石之门》这种有深度的动漫",
    "游戏的话最近在玩《原神》，每天做做日常",
    "有时候会觉得孤独，但大部分时间还挺享受独处的",
    "对未来没什么大志向，平平淡淡就好",
    "恋爱嘛...随缘吧，一个人也挺好的",
]

async def interactive_test():
    """交互式测试：一问一答"""
    user_id = "interactive_test_user"
    
    async with aiohttp.ClientSession() as session:
        print("="*70)
        print("交互式对话测试 - 一问一答模式")
        print("="*70)
        print(f"用户设定：{USER_PROFILE['name']}, {USER_PROFILE['age']}岁，{USER_PROFILE['occupation']}")
        print(f"爱好：{', '.join(USER_PROFILE['hobbies'])}")
        print(f"居住地：{USER_PROFILE['living_city']}")
        print("="*70)
        print()
        
        for i, message in enumerate(CONVERSATIONS, 1):
            print(f"\n{'='*70}")
            print(f"第 {i}/{len(CONVERSATIONS)} 轮对话")
            print(f"{'='*70}")
            print(f"\n🧑 用户：{message}")
            
            payload = {
                "user_id": user_id,
                "message": message,
                "extract_features": True,
                "deep_think": False
            }
            
            try:
                print(f"\n🤖 AI 思考中...", end="", flush=True)
                
                full_response = ""
                async with session.post("http://localhost:8000/api/stream", json=payload) as response:
                    if response.status == 200:
                        # 等待完整响应
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if line.startswith('data: '):
                                data = json.loads(line[6:])
                                
                                if data.get('type') == 'start':
                                    print("\n🤖 AI：", end="", flush=True)
                                
                                elif data.get('type') == 'chunk':
                                    chunk = data.get('content', '')
                                    print(chunk, end="", flush=True)
                                    full_response += chunk
                                
                                elif data.get('type') == 'done':
                                    if full_response:
                                        print()  # 换行
                                    break
                                
                                elif data.get('type') == 'error':
                                    print(f"\n错误：{data.get('content')}")
                                    break
                    else:
                        print(f"\n请求失败：{response.status}")
                        
            except Exception as e:
                print(f"\n异常：{e}")
            
            # 等待 1 秒，让特征提取完成
            await asyncio.sleep(1)
            
            # 显示进度
            print(f"✅ 第 {i} 轮对话完成")
        
        # 所有对话完成
        print(f"\n\n{'='*70}")
        print("所有对话完成！等待特征提取...")
        print(f"{'='*70}")
        await asyncio.sleep(5)
        
        # 获取用户画像
        print(f"\n\n{'='*70}")
        print("获取用户画像结果...")
        print(f"{'='*70}")
        
        async with session.get(f"http://localhost:8000/api/profile/{user_id}") as response:
            if response.status == 200:
                profile = await response.json()
                
                print(f"\n📊 用户画像统计:")
                print(f"  - 用户 ID: {profile.get('user_id')}")
                print(f"  - 特征数量：{len(profile.get('features', []))}")
                print(f"  - 对话数量：{profile.get('summary', {}).get('conversation_count', 0)}")
                
                # 按类型显示特征
                features = profile.get('features', [])
                if features:
                    print(f"\n📋 特征列表:")
                    features_by_type = {}
                    for f in features:
                        ftype = f.get('feature_type', '未知')
                        if ftype not in features_by_type:
                            features_by_type[ftype] = []
                        features_by_type[ftype].append(f)
                    
                    for ftype, flist in features_by_type.items():
                        print(f"\n  【{ftype}】")
                        for f in flist:
                            confidence = f.get('confidence', 0)
                            value = f.get('feature_value', '')
                            print(f"    - {value} (置信度：{confidence:.2f})")
                else:
                    print(f"\n⚠️  没有提取到任何特征！")
                
                print(f"\n{'='*70}")
                
            else:
                print(f"获取用户画像失败：{response.status}")
        
        # 获取知识图谱
        print(f"\n{'='*70}")
        print("获取知识图谱数据...")
        print(f"{'='*70}")
        
        async with session.get(f"http://localhost:8000/api/knowledge-graph/{user_id}") as response:
            if response.status == 200:
                kg = await response.json()
                print(f"\n🕸️  知识图谱:")
                print(f"  - 节点数：{len(kg.get('nodes', []))}")
                print(f"  - 边数：{len(kg.get('edges', []))}")
                print(f"  - 特征类型：{kg.get('featureTypes', [])}")
                
                print(f"\n  节点列表:")
                for node in kg.get('nodes', []):
                    print(f"    - [{node['type']}] {node['label']}")
                
                print(f"\n  边列表:")
                for edge in kg.get('edges', []):
                    inferred = "推断" if edge.get('inferred') else "直接"
                    print(f"    - {edge['source']} -> {edge['target']} ({edge['relation']}) [{inferred}]")
            else:
                print(f"获取知识图谱失败：{response.status}")
        
        print(f"\n{'='*70}")
        print("✅ 测试完成！")
        print(f"{'='*70}")
        print(f"\n💡 提示：")
        print(f"  - 访问前端查看可视化效果：http://localhost:3000/knowledge-graph")
        print(f"  - 用户 ID: {user_id}")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    print("🚀 启动交互式对话测试...\n")
    print("测试模式：一问一答（发送消息 → 等待回复 → 发送下一条）")
    print(f"对话轮数：{len(CONVERSATIONS)} 轮\n")
    
    try:
        asyncio.run(interactive_test())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n⚠️  测试出错：{e}")
        import traceback
        traceback.print_exc()
