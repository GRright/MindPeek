import asyncio
import aiohttp
import json


async def test_chat_endpoint():
    """Test the chat endpoint"""
    url = "http://localhost:8000/api/chat"
    
    test_data = {
        "user_id": "test_user_123",
        "message": "你好！我喜欢周末看书，不太喜欢热闹的聚会。",
        "session_id": "test_session_123",
        "extract_features": True,
        "deep_think": False
    }
    
    print(f"Testing chat endpoint with data: {test_data}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=test_data) as response:
                print(f"Response status: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    print("Success! Response:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    return True
                else:
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    return False
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_endpoint():
    """Test the health endpoint"""
    url = "http://localhost:8000/api/health"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"Health check status: {response.status}")
                if response.status == 200:
                    result = await response.json()
                    print(f"Health check result: {result}")
                    return True
                return False
    except Exception as e:
        print(f"Health check failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing MindPeek API endpoints")
    print("=" * 60)
    
    print("\n1. Testing health endpoint...")
    health_ok = asyncio.run(test_health_endpoint())
    
    if health_ok:
        print("\n2. Testing chat endpoint...")
        asyncio.run(test_chat_endpoint())
    else:
        print("\nHealth check failed, skipping chat test")
    
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)
