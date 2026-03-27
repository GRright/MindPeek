"""
模拟宅男形象与 AI 进行 100+ 轮真实对话测试
用户设定：爱看书和动漫的宅男
"""

import asyncio
import aiohttp
import json
import random
from typing import List, Dict

# 用户画像设定
USER_PROFILE = {
    "name": "小明",
    "age": 25,
    "gender": "男",
    "occupation": "程序员",
    "personality": "内向、理性、喜欢独处",
    "hobbies": ["看书", "动漫", "游戏", "编程"],
    "living_city": "上海",
    "favorite_books": ["三体", "哈利波特", "指环王", "1984"],
    "favorite_anime": ["进击的巨人", "海贼王", "鬼灭之刃", "命运石之门"],
    "work_style": "喜欢远程办公",
    "social_style": "朋友不多但关系很好",
    "sleep_habit": "经常熬夜",
    "food_preference": "喜欢外卖和速食",
    "exercise_habit": "很少运动",
}

# 对话场景和话题库
CONVERSATION_TOPICS = [
    # 书籍相关
    {"topic": "最近在读什么书", "messages": [
        "最近在看什么书啊？",
        "有推荐的书吗？",
        "你喜欢看什么类型的书？",
        "最近有什么好书推荐？",
        "你觉得三体怎么样？",
        "科幻小说你最喜欢哪部？",
    ]},
    
    # 动漫相关
    {"topic": "动漫讨论", "messages": [
        "最近在看什么动漫？",
        "进击的巨人最终季你看了吗？",
        "你最喜欢的动漫角色是谁？",
        "有什么好看的动漫推荐？",
        "你觉得鬼灭之刃怎么样？",
        "动漫对你来说意味着什么？",
    ]},
    
    # 工作相关
    {"topic": "工作日常", "messages": [
        "今天工作怎么样？",
        "你喜欢现在的工作吗？",
        "平时加班多吗？",
        "你喜欢远程办公还是去公司？",
        "工作中遇到的最大挑战是什么？",
        "你有想过换工作吗？",
    ]},
    
    # 生活习惯
    {"topic": "日常生活", "messages": [
        "平时几点睡觉？",
        "周末一般怎么过？",
        "喜欢自己做饭还是点外卖？",
        "平时运动吗？",
        "有什么特别的习惯吗？",
        "宅在家里会无聊吗？",
    ]},
    
    # 社交相关
    {"topic": "社交生活", "messages": [
        "朋友多吗？",
        "周末会和朋友们出去玩吗？",
        "你喜欢社交活动吗？",
        "有参加什么社团或者兴趣小组吗？",
        "觉得社交累不累？",
        "更喜欢独处还是和人在一起？",
    ]},
    
    # 游戏相关
    {"topic": "游戏讨论", "messages": [
        "最近在玩什么游戏？",
        "喜欢单机还是网游？",
        "玩游戏多久了？",
        "最喜欢的游戏是什么？",
        "会为了玩游戏熬夜吗？",
        "游戏对你来说意味着什么？",
    ]},
    
    # 未来规划
    {"topic": "未来打算", "messages": [
        "对未来有什么规划？",
        "有想过换城市生活吗？",
        "想不想谈恋爱？",
        "理想的生活状态是什么样的？",
        "有什么想实现的目标吗？",
        "5 年后想成为什么样的人？",
    ]},
    
    # 心情情感
    {"topic": "心情分享", "messages": [
        "今天心情怎么样？",
        "最近有什么开心的事吗？",
        "有什么烦心事吗？",
        "压力大的时候会做什么？",
        "会觉得孤独吗？",
        "有什么想倾诉的吗？",
    ]},
    
    # 兴趣爱好深挖
    {"topic": "兴趣深挖", "messages": [
        "为什么喜欢看动漫？",
        "看书能给你带来什么？",
        "有没有因为爱好认识新朋友？",
        "爱好对你的工作有帮助吗？",
        "会为了爱好花钱吗？",
        "爱好会影响你的生活吗？",
    ]},
    
    # 回忆过去
    {"topic": "回忆往事", "messages": [
        "小时候喜欢看什么动漫？",
        "第一本印象深刻的书是什么？",
        "学生时代是什么样子的？",
        "有没有后悔的事情？",
        "最怀念的时光是什么时候？",
        "过去有什么特别的经历？",
    ]},
]

# 宅男典型回复模板
OTAKU_RESPONSES = {
    "books": [
        "最近在看《三体》，刘慈欣的想象力真的太强了，黑暗森林法则让我思考了很久。",
        "刚重读完《哈利波特》，每次看都有新的感受，魔法世界真的很吸引人。",
        "最近在看一些科幻小说，感觉比看动漫更有沉浸感。",
        "书是我最好的朋友，看书的时候可以完全沉浸在自己的世界里。",
        "我喜欢看那种有深度、能让人思考的书，比如《1984》这种。",
    ],
    
    "anime": [
        "最近在追《进击的巨人》最终季，剧情太震撼了，谏山创真的是天才。",
        "《命运石之门》是我看过最神的作品，时间旅行的设定太烧脑了。",
        "动漫对我来说不仅仅是娱乐，更是一种精神寄托。",
        "周末一般就宅在家里看动漫，一看看一整天。",
        "我比较喜欢那种有深度剧情的动漫，比如《进击的巨人》、《命运石之门》这种。",
    ],
    
    "work": [
        "工作还好吧，我是程序员，平时就写写代码，挺适合我的性格的。",
        "我喜欢远程办公，不用和人打交道，效率也高。",
        "加班挺多的，不过我习惯了，反正回家也是一个人。",
        "工作就是为了生活，但我的生活要求不高，够花就行。",
        "有时候会觉得工作没什么意义，但这就是现实吧。",
    ],
    
    "life": [
        "我一般凌晨 2 点左右睡觉，白天起不来。",
        "周末就宅在家里，看看动漫打打游戏，很充实。",
        "吃饭基本都是外卖，自己不会做饭也不想学。",
        "很少运动，感觉身体还行吧，就是容易累。",
        "我挺享受一个人独处的时光的，很自在。",
    ],
    
    "social": [
        "朋友不多，就几个，但关系都很好。",
        "不太喜欢社交活动，感觉很累。",
        "周末一般不会出门，就在家里待着。",
        "我觉得独处比和人在一起更舒服。",
        "有社交恐惧症，人多的场合会不自在。",
    ],
    
    "games": [
        "最近在玩《原神》，每天上线做做日常。",
        "我比较喜欢单机游戏，不用和人交流。",
        "玩游戏能让我忘记现实的烦恼。",
        "会为了玩游戏熬夜，有时候一玩玩到天亮。",
        "游戏是我生活中很重要的一部分。",
    ],
    
    "future": [
        "未来就想这样平平淡淡的生活，没什么大志向。",
        "想换个工作环境，但懒得动。",
        "恋爱嘛...随缘吧，感觉一个人也挺好的。",
        "理想的生活就是有花不完的钱，然后天天宅在家里。",
        "没什么特别的目标，过好每一天就行。",
    ],
    
    "mood": [
        "今天心情还行，和平时一样。",
        "开心的事...今天看的动漫很好看算吗？",
        "烦心事挺多的，但都习惯了。",
        "压力大的时候就看看动漫打打游戏。",
        "偶尔会觉得孤独，但大部分时间还好。",
    ],
}


async def simulate_conversation(session: aiohttp.ClientSession, user_id: str, num_rounds: int = 100):
    """模拟多轮对话"""
    messages = []
    topic_index = 0
    
    print(f"\n{'='*60}")
    print(f"开始模拟对话测试，共 {num_rounds} 轮")
    print(f"用户画像：{USER_PROFILE['name']}, {USER_PROFILE['age']}岁，{USER_PROFILE['occupation']}")
    print(f"{'='*60}\n")
    
    for round_num in range(1, num_rounds + 1):
        # 选择话题
        topic = CONVERSATION_TOPICS[topic_index % len(CONVERSATION_TOPICS)]
        user_message = random.choice(topic["messages"])
        
        # 根据话题类型选择更符合用户画像的回复
        if "书" in user_message or "书" in user_message:
            response = random.choice(OTAKU_RESPONSES["books"])
        elif "动漫" in user_message or "动漫" in user_message:
            response = random.choice(OTAKU_RESPONSES["anime"])
        elif "工作" in user_message or "工作" in user_message:
            response = random.choice(OTAKU_RESPONSES["work"])
        elif "生活" in user_message or "周末" in user_message or "睡觉" in user_message:
            response = random.choice(OTAKU_RESPONSES["life"])
        elif "朋友" in user_message or "社交" in user_message:
            response = random.choice(OTAKU_RESPONSES["social"])
        elif "游戏" in user_message:
            response = random.choice(OTAKU_RESPONSES["games"])
        elif "未来" in user_message or "理想" in user_message:
            response = random.choice(OTAKU_RESPONSES["future"])
        elif "心情" in user_message:
            response = random.choice(OTAKU_RESPONSES["mood"])
        else:
            # 随机选择一个回复
            all_responses = []
            for responses in OTAKU_RESPONSES.values():
                all_responses.extend(responses)
            response = random.choice(all_responses)
        
        # 添加一些个性化信息
        if round_num == 1:
            response = "你好，我叫小明，是个程序员。平时比较宅，喜欢看看书和动漫。"
        elif round_num == 10:
            response = "我住在上海，这里的生活节奏挺快的，不过我平时也不太出门。"
        elif round_num == 20:
            response = "我最喜欢《三体》和《进击的巨人》，这两部作品都很有深度。"
        elif round_num == 30:
            response = "我经常熬夜，一般凌晨 2 点才睡，早上起不来。"
        elif round_num == 40:
            response = "朋友不多，就三四个吧，但都是认识很多年的老朋友了。"
        elif round_num == 50:
            response = "不太喜欢运动，感觉挺无聊的，宁愿在家看动漫。"
        elif round_num == 60:
            response = "远程办公挺好的，不用和人打交道，效率也高。"
        elif round_num == 70:
            response = "吃饭基本都是外卖，自己不会做饭，也不想学。"
        elif round_num == 80:
            response = "游戏是我生活中很重要的一部分，不玩游戏都不知道干嘛了。"
        elif round_num == 90:
            response = "恋爱嘛...随缘吧，感觉一个人也挺好的，自由自在。"
        elif round_num == 100:
            response = "和你聊天挺开心的，虽然我是 AI，但感觉你挺理解我的。"
        
        messages.append({
            "round": round_num,
            "user": user_message,
            "assistant": response
        })
        
        # 发送到 API
        try:
            await send_message_to_api(session, user_id, response)
            print(f"第 {round_num} 轮对话完成")
        except Exception as e:
            print(f"第 {round_num} 轮对话失败：{e}")
        
        # 切换话题
        if round_num % 10 == 0:
            topic_index += 1
        
        # 短暂延迟，模拟真实对话
        await asyncio.sleep(random.uniform(0.5, 2.0))
    
    return messages


async def send_message_to_api(session: aiohttp.ClientSession, user_id: str, message: str):
    """发送消息到 API"""
    url = "http://localhost:8000/api/stream"
    
    payload = {
        "user_id": user_id,
        "message": message,
        "extract_features": True,
        "deep_think": False
    }
    
    async with session.post(url, json=payload) as response:
        if response.status == 200:
            # 读取流式响应
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = json.loads(line[6:])
                    if data.get('type') == 'done':
                        return data
        else:
            raise Exception(f"API 返回错误：{response.status}")


async def main():
    """主函数"""
    user_id = "test_otaku_user"
    num_rounds = 100
    
    # 创建 HTTP 会话
    connector = aiohttp.TCPConnector(limit=10)
    async with aiohttp.ClientSession(connector=connector) as session:
        # 模拟对话
        messages = await simulate_conversation(session, user_id, num_rounds)
        
        # 保存对话记录
        with open(f"conversation_log_{user_id}.json", "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"对话测试完成！共完成 {len(messages)} 轮对话")
        print(f"对话记录已保存到：conversation_log_{user_id}.json")
        print(f"{'='*60}\n")
        
        # 等待一段时间让特征提取完成
        print("等待特征提取完成...")
        await asyncio.sleep(5)
        
        # 获取用户画像
        print("\n获取用户画像...")
        await get_user_profile(session, user_id)


async def get_user_profile(session: aiohttp.ClientSession, user_id: str):
    """获取用户画像"""
    url = f"http://localhost:8000/api/user/{user_id}/features"
    
    async with session.get(url) as response:
        if response.status == 200:
            features = await response.json()
            print("\n" + "="*60)
            print("用户画像特征:")
            print("="*60)
            
            # 按类型分组显示
            features_by_type = {}
            for feature in features:
                feature_type = feature.get("feature_type", "未知")
                if feature_type not in features_by_type:
                    features_by_type[feature_type] = []
                features_by_type[feature_type].append(feature)
            
            for feature_type, type_features in features_by_type.items():
                print(f"\n【{feature_type}】")
                for feature in type_features:
                    confidence = feature.get("confidence", 0)
                    value = feature.get("feature_value", "")
                    print(f"  - {value} (置信度：{confidence:.2f})")
            
            print("="*60)
        else:
            print(f"获取用户画像失败：{response.status}")


if __name__ == "__main__":
    print("开始模拟宅男形象对话测试...")
    print("用户设定：25 岁男性程序员，爱看书和动漫，性格内向")
    print("预计对话轮数：100 轮")
    print("\n请确保后端服务已启动 (http://localhost:8000)")
    print("按 Ctrl+C 可以随时停止测试\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n测试出错：{e}")
        print("\n请确保：")
        print("1. 后端服务已启动：python -m uvicorn main:app --host 0.0.0.0 --port 8000")
        print("2. 配置文件已正确设置 LLM API")
