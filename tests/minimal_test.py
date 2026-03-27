"""
最小化测试 - 直接调用 API 并查看详细错误
"""

import asyncio
import aiohttp
import json

async def minimal_test():
    user_id = "minimal_test_user"
    message = "你好，我是个程序员"
    
    async with aiohttp.ClientSession() as session:
        print("发送单条消息测试...\n")
        
        payload = {
            "user_id": user_id,
            "message": message,
            "extract_features": True,
            "deep_think": False
        }
        
        try:
            async with session.post("http://localhost:8000/api/stream", json=payload) as response:
                print(f"状态码：{response.status}")
                
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    print(f"响应：{line}")
                    
        except Exception as e:
            print(f"错误：{e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(3)
        
        # 检查数据库
        print("\n\n检查数据库...")
        try:
            async with session.get(f"http://localhost:8000/api/profile/{user_id}") as response:
                print(f"状态码：{response.status}")
                if response.status == 200:
                    profile = await response.json()
                    print(f"用户 ID: {profile.get('user_id')}")
                    print(f"特征数量：{len(profile.get('features', []))}")
                    print(f"对话数量：{profile.get('summary', {}).get('conversation_count', 0)}")
                    print(json.dumps(profile, ensure_ascii=False, indent=2))
                else:
                    print(f"获取失败：{response.status}")
        except Exception as e:
            print(f"错误：{e}")

if __name__ == "__main__":
    asyncio.run(minimal_test())
