"""
LLM提供者模块 - 支持多种大模型
"""
import os
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import httpx
from ..core.config import config_manager, LLMProviderConfig


class BaseLLMProvider(ABC):
    """LLM提供者基类"""
    
    def __init__(self, config: LLMProviderConfig):
        self.config = config
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """发送聊天请求"""
        pass
    
    @abstractmethod
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        """流式聊天"""
        pass


class QwenProvider(BaseLLMProvider):
    """通义千问提供者"""
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.config.api_key or os.getenv("DASHSCOPE_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model or "qwen-turbo",
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.config.api_url or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        api_key = self.config.api_key or os.getenv("DASHSCOPE_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model or "qwen-turbo",
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                self.config.api_url or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            try:
                                chunk = json.loads(data)
                                if chunk["choices"][0].get("delta", {}).get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                continue


class YiProvider(BaseLLMProvider):
    """智谱AI/Yi提供者"""
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.config.api_key or os.getenv("YI_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model or "yi-light",
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.config.api_url or "https://api.lingyiwanwu.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        api_key = self.config.api_key or os.getenv("YI_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model or "yi-light",
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                self.config.api_url or "https://api.lingyiwanwu.com/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            try:
                                chunk = json.loads(data)
                                if chunk["choices"][0].get("delta", {}).get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                continue


class ERNIEProvider(BaseLLMProvider):
    """文心一言提供者"""
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.config.api_key or os.getenv("ERNIE_API_KEY")
        access_token = await self._get_access_token(api_key)
        
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "model": self.config.model or "ernie-4.0-8k",
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_output_tokens": kwargs.get("max_tokens", self.config.max_tokens)
        }
        
        api_url = self.config.api_url or "https://qianfan.baidubce.com/v2/chat/completions"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{api_url}?access_token={access_token}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["result"]
    
    async def _get_access_token(self, api_key: str) -> str:
        parts = api_key.split(":") if ":" in api_key else [api_key, ""]
        client_id = parts[0]
        client_secret = parts[1] if len(parts) > 1 else ""
        
        auth_url = "https://aip.baidubce.com/oauth/2.0/token"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                auth_url,
                params={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret
                }
            )
            response.raise_for_status()
            return response.json()["access_token"]
    
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        api_key = self.config.api_key or os.getenv("ERNIE_API_KEY")
        access_token = await self._get_access_token(api_key)
        
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "model": self.config.model or "ernie-4.0-8k",
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_output_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True
        }
        
        api_url = self.config.api_url or "https://qianfan.baidubce.com/v2/chat/completions"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{api_url}?access_token={access_token}",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            chunk = json.loads(data)
                            if "result" in chunk:
                                yield chunk["result"]
                        except json.JSONDecodeError:
                            continue


class OllamaProvider(BaseLLMProvider):
    """Ollama本地模型提供者"""
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        payload = {
            "model": self.config.model or "llama3",
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens)
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.config.api_url or "http://localhost:11434/api/chat",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["message"]["content"]
    
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        payload = {
            "model": self.config.model or "llama3",
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens)
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                self.config.api_url or "http://localhost:11434/api/chat",
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and chunk["message"].get("content"):
                            yield chunk["message"]["content"]
                    except json.JSONDecodeError:
                        continue


class OpenAIProvider(BaseLLMProvider):
    """OpenAI提供者"""
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model or "gpt-4",
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.config.api_url or "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.config.model or "gpt-4",
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                self.config.api_url or "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            try:
                                chunk = json.loads(data)
                                if chunk["choices"][0].get("delta", {}).get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                continue


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter提供者 - 支持多种模型"""
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        api_key = self.config.api_key or os.getenv("OPENROUTER_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/",
            "X-Title": "perMIR User Profile System"
        }
        
        payload = {
            "model": self.config.model or "stepfun/step-3.5-flash:free",
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens)
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.config.api_url or "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def chat_stream(self, messages: List[Dict[str, str]], **kwargs):
        api_key = self.config.api_key or os.getenv("OPENROUTER_API_KEY")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/",
            "X-Title": "perMIR User Profile System"
        }
        
        payload = {
            "model": self.config.model or "stepfun/step-3.5-flash:free",
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                self.config.api_url or "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            try:
                                chunk = json.loads(data)
                                if chunk["choices"][0].get("delta", {}).get("content"):
                                    yield chunk["choices"][0]["delta"]["content"]
                            except json.JSONDecodeError:
                                continue


class LLMProviderFactory:
    """LLM提供者工厂"""
    
    _providers = {
        "qwen": QwenProvider,
        "yi": YiProvider,
        "ERNIE": ERNIEProvider,
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "openrouter": OpenRouterProvider,
    }
    
    _instances: Dict[str, BaseLLMProvider] = {}
    
    @classmethod
    def get_provider(cls, provider_type: str) -> BaseLLMProvider:
        if provider_type in cls._instances:
            return cls._instances[provider_type]
        
        config = config_manager.get_llm_config(provider_type)
        provider_class = cls._providers.get(provider_type, QwenProvider)
        instance = provider_class(config)
        cls._instances[provider_type] = instance
        return instance
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        return list(cls._providers.keys())
    
    @classmethod
    def clear_instances(cls):
        cls._instances.clear()
