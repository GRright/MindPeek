"""
调试测试 - 查看详细的请求和响应
"""

import asyncio
import aiohttp

async def debug_test():
    """调试测试"""
    user_id = "debug_user"
    message = "你好，我是个程序员，喜欢看书"
    
    print("="*60)
    print("调试测试 - 查看详细请求响应")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        print(f"\n发送请求到：http://localhost:8000/api/stream")
        print(f"用户 ID: {user_id}")
        print(f"消息：{message}")
        
        payload = {
            "user_id": user_id,
            "message": message,
            "extract_features": True,
            "deep_think": False
        }
        
        try:
            print("\n发送 POST 请求...")
            async with session.post("http://localhost:8000/api/stream", json=payload) as response:
                print(f"响应状态码：{response.status}")
                print(f"响应头：{response.headers}")
                
                print("\n读取流式响应:")
                async for line in response.content:
                    line = line.decode('utf-8').strip()
                    print(f"  {line}")
                    
        except Exception as e:
            print(f"异常：{e}")
            import traceback
            traceback.print_exc()
        
        # 等待 3 秒
        print("\n等待 3 秒...")
        await asyncio.sleep(3)
        
        # 获取用户画像
        print("\n获取用户画像...")
        try:
            async with session.get(f"http://localhost:8000/api/profile/{user_id}") as response:
                print(f"响应状态码：{response.status}")
                if response.status == 200:
                    profile = await response.json()
                    print(f"用户 ID: {profile.get('user_id')}")
                    print(f"特征数量：{len(profile.get('features', []))}")
                else:
                    print(f"获取失败：{response.status}")
        except Exception as e:
            print(f"异常：{e}")

if __name__ == "__main__":
    asyncio.run(debug_test())
