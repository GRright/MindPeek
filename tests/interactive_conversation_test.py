"""
交互式对话测试 - 快速体验 MindPeek 功能
运行此脚本可快速生成用户画像、智能提醒和趋势分析
"""

import asyncio
import aiohttp
import json

USER_PROFILE = {
    "name": "小明",
    "age": 25,
    "gender": "男",
    "occupation": "程序员",
    "hobbies": ["看书", "动漫", "游戏"],
    "living_city": "上海",
}

CONVERSATIONS = [
    "你好，我叫小明，是个程序员，今年25岁",
    "我平时比较宅，喜欢看看书和动漫",
    "最近在看《三体》，刘慈欣的想象力太强了",
    "周末一般就宅在家里看动漫，一看看一整天",
    "我住在上海，这里的生活节奏挺快的",
    "朋友不多，就几个大学同学，但关系都很好",
    "我一般凌晨2点左右睡觉，白天起不来",
    "吃饭基本都是外卖，自己不会做饭也不想学",
    "不太喜欢运动，感觉挺无聊的",
    "远程办公挺好的，不用和人打交道，效率也高",
    "最喜欢《进击的巨人》和《命运石之门》这种有深度的动漫",
    "游戏的话最近在玩《原神》，每天做做日常",
    "有时候会觉得孤独，但大部分时间还挺享受独处的",
    "对未来没什么大志向，平平淡淡就好",
    "恋爱嘛...随缘吧，一个人也挺好的",
    "最近工作压力有点大，项目赶进度",
    "有时候会感到焦虑，担心自己技术跟不上",
    "昨天又加班到很晚，感觉有点累",
    "父母在老家，偶尔打个电话，关系还行",
    "我是INTP类型的，测过好几次都是",
    "我觉得人生的意义就是做自己喜欢的事",
    "最近心情不太好，有点郁闷",
    "有时候会感到孤独，特别是周末一个人在家的时候",
    "工作上遇到一些困难，有点焦虑",
    "不过看看动漫心情就好多了",
    "我比较内向，不太擅长社交",
    "喜欢安静的环境，人多会觉得累",
    "思考问题比较理性，不喜欢感性决策",
    "对于未来，我希望能找到一份稳定的工作",
    "最近在考虑要不要换个城市生活",
]

async def interactive_test():
    """交互式测试：一问一答"""
    user_id = "MindPeek"
    
    async with aiohttp.ClientSession() as session:
        print("="*70)
        print("MindPeek 交互式对话测试")
        print("="*70)
        print(f"用户设定：{USER_PROFILE['name']}, {USER_PROFILE['age']}岁，{USER_PROFILE['occupation']}")
        print(f"爱好：{', '.join(USER_PROFILE['hobbies'])}")
        print(f"居住地：{USER_PROFILE['living_city']}")
        print(f"对话轮数：{len(CONVERSATIONS)} 轮")
        print("="*70)
        print()
        
        for i, message in enumerate(CONVERSATIONS, 1):
            print(f"\n{'='*70}")
            print(f"第 {i}/{len(CONVERSATIONS)} 轮对话")
            print(f"{'='*70}")
            print(f"\n用户：{message}")
            
            payload = {
                "user_id": user_id,
                "message": message,
                "extract_features": True,
                "deep_think": False
            }
            
            try:
                print(f"\nAI 思考中...", end="", flush=True)
                
                full_response = ""
                async with session.post("http://localhost:8000/api/stream", json=payload) as response:
                    if response.status == 200:
                        async for line in response.content:
                            line = line.decode('utf-8').strip()
                            if line.startswith('data: '):
                                data = json.loads(line[6:])
                                
                                if data.get('type') == 'start':
                                    print("\nAI：", end="", flush=True)
                                
                                elif data.get('type') == 'chunk':
                                    chunk = data.get('content', '')
                                    print(chunk, end="", flush=True)
                                    full_response += chunk
                                
                                elif data.get('type') == 'done':
                                    if full_response:
                                        print()
                                    break
                                
                                elif data.get('type') == 'error':
                                    print(f"\n错误：{data.get('content')}")
                                    break
                    else:
                        print(f"\n请求失败：{response.status}")
                        
            except Exception as e:
                print(f"\n异常：{e}")
            
            await asyncio.sleep(0.5)
            print(f"第 {i} 轮对话完成")
        
        print(f"\n\n{'='*70}")
        print("所有对话完成！等待特征提取...")
        print(f"{'='*70}")
        await asyncio.sleep(3)
        
        print(f"\n\n{'='*70}")
        print("获取用户画像结果...")
        print(f"{'='*70}")
        
        async with session.get(f"http://localhost:8000/api/profile/{user_id}") as response:
            if response.status == 200:
                profile = await response.json()
                
                print(f"\n用户画像统计:")
                print(f"  - 用户 ID: {profile.get('user_id')}")
                print(f"  - 特征数量：{len(profile.get('features', []))}")
                print(f"  - 对话数量：{profile.get('summary', {}).get('conversation_count', 0)}")
                
                features = profile.get('features', [])
                if features:
                    print(f"\n特征列表:")
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
                            print(f"    - {value} (置信度：{confidence:.0%})")
                else:
                    print(f"\n没有提取到任何特征！")
                
                print(f"\n{'='*70}")
                
            else:
                print(f"获取用户画像失败：{response.status}")
        
        print(f"\n\n{'='*70}")
        print("获取智能提醒和画像趋势...")
        print(f"{'='*70}")
        
        async with session.get(f"http://localhost:8000/api/profile/{user_id}/insights") as response:
            if response.status == 200:
                insights = await response.json()
                
                alerts = insights.get('alerts', [])
                stats = insights.get('stats', {})
                
                if alerts:
                    print(f"\n智能提醒 ({len(alerts)} 条):")
                    for alert in alerts:
                        level_icon = {"warning": "!", "serious": "!!", "info": "*"}
                        print(f"  [{level_icon.get(alert['level'], '-')}] {alert['title']}")
                        print(f"      {alert['message']}")
                else:
                    print(f"\n暂无智能提醒")
                
                print(f"\n统计数据:")
                print(f"  - 总特征数：{stats.get('total_features', 0)}")
                
            else:
                print(f"获取洞察失败：{response.status}")
        
        print(f"\n\n{'='*70}")
        print("获取知识图谱数据...")
        print(f"{'='*70}")
        
        async with session.get(f"http://localhost:8000/api/knowledge-graph/{user_id}") as response:
            if response.status == 200:
                kg = await response.json()
                print(f"\n知识图谱:")
                print(f"  - 节点数：{len(kg.get('nodes', []))}")
                print(f"  - 边数：{len(kg.get('edges', []))}")
                print(f"  - 特征类型：{kg.get('featureTypes', [])}")
            else:
                print(f"获取知识图谱失败：{response.status}")
        
        print(f"\n\n{'='*70}")
        print("测试完成！")
        print(f"{'='*70}")
        print(f"\n提示：")
        print(f"  - 前端界面：http://localhost:3000")
        print(f"  - 知识图谱：http://localhost:3000/knowledge-graph")
        print(f"  - 特征管理：http://localhost:3000/features")
        print(f"  - 用户 ID: {user_id}")
        print(f"{'='*70}\n")

if __name__ == "__main__":
    print("启动交互式对话测试...\n")
    print("此测试将：")
    print("  1. 发送多轮对话，自动提取用户特征")
    print("  2. 生成用户画像和知识图谱")
    print("  3. 触发智能提醒和画像趋势分析")
    print()
    
    try:
        asyncio.run(interactive_test())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n测试出错：{e}")
        import traceback
        traceback.print_exc()
