"""
配置管理模块
"""
import os
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class LLMProviderConfig(BaseModel):
    enabled: bool = True
    api_key: str = ""
    api_url: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 2000


class FeatureExtractionConfig(BaseModel):
    confidence_threshold: float = 0.6
    auto_update_on_new_message: bool = True
    max_history_messages: int = 100
    enable_knowledge_graph: bool = True
    enable_multi_agent: bool = True


class Settings(BaseSettings):
    app_name: str = "perMIR - 用户画像生成系统"
    app_version: str = "2.0.0"
    debug: bool = True
    
    database_url: str = "sqlite+aiosqlite:///./data/permir.db"
    
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    default_llm_provider: str = "qwen"
    
    class Config:
        env_file = ".env"


class ConfigManager:
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self.load_config()
    
    def load_config(self, config_path: str = "config/config.json") -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, config_path)
        
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        else:
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "llm_providers": {
                "qwen": {
                    "enabled": True,
                    "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
                    "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                    "model": "qwen-turbo",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "yi": {
                    "enabled": True,
                    "api_key": os.getenv("YI_API_KEY", ""),
                    "api_url": "https://api.lingyiwanwu.com/v1/chat/completions",
                    "model": "yi-light",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "ERNIE": {
                    "enabled": True,
                    "api_key": os.getenv("ERNIE_API_KEY", ""),
                    "api_url": "https://qianfan.baidubce.com/v2/chat/completions",
                    "model": "ernie-4.0-8k",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "ollama": {
                    "enabled": True,
                    "api_url": "http://localhost:11434/api/chat",
                    "model": "llama3",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "openai": {
                    "enabled": False,
                    "api_key": os.getenv("OPENAI_API_KEY", ""),
                    "api_url": "https://api.openai.com/v1/chat/completions",
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "openrouter": {
                    "enabled": True,
                    "api_key": os.getenv("OPENROUTER_API_KEY", ""),
                    "api_url": "https://openrouter.ai/api/v1/chat/completions",
                    "model": "stepfun/step-3.5-flash:free",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            },
            "default_provider": "openrouter",
            "feature_extraction": {
                "confidence_threshold": 0.6,
                "auto_update_on_new_message": True,
                "max_history_messages": 100,
                "enable_knowledge_graph": True,
                "enable_multi_agent": True
            }
        }
    
    def get_llm_config(self, provider: str) -> LLMProviderConfig:
        providers = self._config.get("llm_providers", {})
        config = providers.get(provider, {})
        return LLMProviderConfig(**config)
    
    def get_feature_config(self) -> FeatureExtractionConfig:
        config = self._config.get("feature_extraction", {})
        return FeatureExtractionConfig(**config)
    
    def get_default_provider(self) -> str:
        return self._config.get("default_provider", "qwen")
    
    def update_llm_config(self, provider: str, api_key: str = None, **kwargs) -> None:
        if provider not in self._config["llm_providers"]:
            self._config["llm_providers"][provider] = {}
        
        if api_key:
            self._config["llm_providers"][provider]["api_key"] = api_key
        
        for key, value in kwargs.items():
            self._config["llm_providers"][provider][key] = value
        
        self.save_config()
    
    def save_config(self, config_path: str = "config/config.json") -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, config_path)
        
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=4)


settings = Settings()
config_manager = ConfigManager()
