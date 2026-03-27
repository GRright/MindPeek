"""
测试 LLM 服务是否可用
"""

import asyncio
import aiohttp

async def test_llm():
    """测试 LLM 服务"""
    
    # 测试配置
    api_url = "http://172.16.5.147:8000/v1"
    api_key = "local-vllm-key"
    model = "deepseek-ai/DeepSeek-R1-Distill-Qwen-14B"
    
    print("="*60)
    print("测试 LLM 服务")
    print("="*60)
    print(f"API URL: {api_url}")
    print(f"Model: {model}")
    print("="*60)
    
    async with aiohttp.ClientSession() as session:
        # 测试 1: 检查模型列表
        print("\n1. 获取模型列表...")
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            async with session.get(f"{api_url}/models", headers=headers) as response:
                print(f"   状态码：{response.status}")
                if response.status == 200:
                    models = await response.json()
                    print(f"   模型列表：{models}")
                else:
                    print(f"   错误：{await response.text()}")
        except Exception as e:
            print(f"   异常：{e}")
        
        # 测试 2: 尝试对话
        print("\n2. 测试对话接口...")
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": "你好"}
                ],
                "stream": False
            }
            async with session.post(f"{api_url}/chat/completions", headers=headers, json=payload) as response:
                print(f"   状态码：{response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"   回复：{result}")
                else:
                    error_text = await response.text()
                    print(f"   错误响应：{error_text}")
        except Exception as e:
            print(f"   异常：{e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm())
