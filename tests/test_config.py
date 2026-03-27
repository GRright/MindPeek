import sys
sys.path.insert(0, 'C:\\myProject\\MindPeek')

from backend.core.config import ConfigManager

cm = ConfigManager()
print("配置加载成功")
print(f"LLM 提供商：{cm._config.get('llm_providers', {}).keys()}")

# 测试 LLMProviderFactory
from backend.services.llm_provider import LLMProviderFactory
llm = LLMProviderFactory.create(cm)
print(f"LLM 创建成功：{type(llm).__name__}")

# 测试调用 LLM
import asyncio
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

print("\n测试 LLM 调用...")
response = loop.run_until_complete(llm.chat([{"role": "user", "content": "你好"}]))
print(f"LLM 响应：{response[:50]}...")
