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


class MemoBaseConfig(BaseModel):
    enabled: bool = False
    project_url: str = ""
    api_key: str = ""


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
            example_path = os.path.join(base_dir, "config/config.example.json")
            raise FileNotFoundError(
                f"配置文件不存在: {full_path}\n"
                f"请复制 config/config.example.json 为 config/config.json 并填写您的配置信息。\n"
                f"示例配置路径: {example_path}"
            )

    def get_llm_config(self, provider: str = None) -> LLMProviderConfig:
        if "llm_provider" in self._config:
            return LLMProviderConfig(**self._config["llm_provider"])
        
        providers = self._config.get("llm_providers", {})
        if provider not in providers:
            available = list(providers.keys())
            raise ValueError(
                f"LLM 提供者 '{provider}' 未在配置文件中定义。\n"
                f"可用的提供者: {available}\n"
                f"请在 config/config.json 的 llm_providers 中配置 '{provider}'。"
            )
        config = providers.get(provider, {})
        return LLMProviderConfig(**config)

    def get_memo_base_config(self) -> MemoBaseConfig:
        config = self._config.get("memo_base", {})
        return MemoBaseConfig(**config)

    def get_feature_config(self) -> FeatureExtractionConfig:
        config = self._config.get("feature_extraction", {})
        return FeatureExtractionConfig(**config)

    def get_database_path(self) -> str:
        db_config = self._config.get("database", {})
        db_path = db_config.get("path", "data/permir.db")
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_dir, db_path)

    def get_default_provider(self) -> str:
        if "default_provider" in self._config:
            return self._config["default_provider"]
        
        providers = self._config.get("llm_providers", {})
        for provider_name, provider_config in providers.items():
            if provider_config.get("enabled", True):
                return provider_name
        
        raise ValueError(
            "未找到可用的 LLM 提供者。\n"
            "请在 config/config.json 中配置 llm_providers 并设置 default_provider。"
        )

    def update_llm_config(self, provider: str, api_key: str = None, **kwargs) -> None:
        if provider not in self._config["llm_providers"]:
            self._config["llm_providers"][provider] = {}

        if api_key:
            self._config["llm_providers"][provider]["api_key"] = api_key

        for key, value in kwargs.items():
            self._config["llm_providers"][provider][key] = value

    def save_config(self, config_path: str = "config/config.json") -> None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, config_path)

        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=4, ensure_ascii=False)


config_manager = ConfigManager()
settings = Settings()