"""
MemoBase 服务 - 用于存储和检索用户画像数据
使用 httpx 直接调用 MemoBase HTTP API
"""
import httpx
import json
from typing import Dict, List, Optional, Any
from ..core.config import config_manager


class MemoBaseService:
    """MemoBase 服务类"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._config = config_manager.get_memo_base_config()
        self._client = None
        self._enabled = self._config.enabled

    def _get_client(self) -> Optional[httpx.AsyncClient]:
        if not self._enabled:
            return None

        if self._client is None:
            if not self._config.project_url or not self._config.api_key:
                print("Warning: MemoBase project_url or api_key not configured")
                return None

            self._client = httpx.AsyncClient(
                base_url=self._config.project_url,
                headers={
                    "Authorization": f"Bearer {self._config.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )

        return self._client

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def is_enabled(self) -> bool:
        """检查 MemoBase 是否启用"""
        return self._enabled and self._get_client() is not None

    async def save_user_profile(self, user_id: str, profile_data: Dict[str, Any],
                                 conversation_summary: str = "") -> bool:
        """保存用户画像到 MemoBase"""
        client = self._get_client()
        if not client:
            return False

        try:
            collection_name = "user_profiles"
            doc_id = f"user_profile_{user_id}"

            document = {
                "user_id": user_id,
                "profile_data": profile_data,
                "conversation_summary": conversation_summary,
                "updated_at": self._get_timestamp()
            }

            response = await client.get(f"/collections/{collection_name}/documents/{doc_id}")
            if response.status_code == 200:
                await client.put(
                    f"/collections/{collection_name}/documents/{doc_id}",
                    json=document
                )
            else:
                await client.post(
                    f"/collections/{collection_name}/documents",
                    json={"doc_id": doc_id, "document": document}
                )

            return True

        except Exception as e:
            print(f"Error saving user profile to MemoBase: {e}")
            return False

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """从 MemoBase 获取用户画像"""
        client = self._get_client()
        if not client:
            return None

        try:
            collection_name = "user_profiles"
            doc_id = f"user_profile_{user_id}"

            response = await client.get(f"/collections/{collection_name}/documents/{doc_id}")

            if response.status_code == 200:
                data = response.json()
                return data.get("document", {})
            return None

        except Exception as e:
            print(f"Error getting user profile from MemoBase: {e}")
            return None

    async def update_conversation(self, user_id: str, role: str,
                                  content: str, session_id: str = "default") -> bool:
        """更新对话历史到 MemoBase"""
        client = self._get_client()
        if not client:
            return False

        try:
            collection_name = "conversations"
            doc_id = f"conv_{user_id}_{session_id}"

            existing = await self._get_conversation_async(user_id, session_id)

            if existing:
                messages = existing.get("messages", [])
                messages.append({"role": role, "content": content, "timestamp": self._get_timestamp()})
                doc = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "messages": messages,
                    "updated_at": self._get_timestamp()
                }
                await client.put(
                    f"/collections/{collection_name}/documents/{doc_id}",
                    json=doc
                )
            else:
                doc = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "messages": [{"role": role, "content": content, "timestamp": self._get_timestamp()}],
                    "updated_at": self._get_timestamp()
                }
                await client.post(
                    f"/collections/{collection_name}/documents",
                    json={"doc_id": doc_id, "document": doc}
                )

            return True

        except Exception as e:
            print(f"Error updating conversation in MemoBase: {e}")
            return False

    async def _get_conversation_async(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """异步获取对话历史"""
        client = self._get_client()
        if not client:
            return None

        try:
            collection_name = "conversations"
            doc_id = f"conv_{user_id}_{session_id}"

            response = await client.get(f"/collections/{collection_name}/documents/{doc_id}")

            if response.status_code == 200:
                data = response.json()
                return data.get("document", {})
            return None

        except Exception:
            return None

    async def search_profiles(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索用户画像"""
        client = self._get_client()
        if not client:
            return []

        try:
            collection_name = "user_profiles"

            response = await client.post(
                f"/collections/{collection_name}/search",
                json={"query": query, "limit": limit}
            )

            if response.status_code == 200:
                return response.json().get("results", [])
            return []

        except Exception as e:
            print(f"Error searching profiles in MemoBase: {e}")
            return []

    async def save_feature(self, user_id: str, feature_type: str,
                           feature_value: str, confidence: float,
                           reasoning: str = "", evidence: str = "") -> bool:
        """保存单个特征到 MemoBase"""
        client = self._get_client()
        if not client:
            return False

        try:
            collection_name = "user_features"
            doc_id = f"feature_{user_id}_{feature_type}_{feature_value}"

            document = {
                "user_id": user_id,
                "feature_type": feature_type,
                "feature_value": feature_value,
                "confidence": confidence,
                "reasoning": reasoning,
                "evidence": evidence,
                "updated_at": self._get_timestamp()
            }

            existing = await self._get_feature_async(user_id, feature_type, feature_value)
            if existing:
                if confidence > existing.get("confidence", 0):
                    await client.put(
                        f"/collections/{collection_name}/documents/{doc_id}",
                        json=document
                    )
            else:
                await client.post(
                    f"/collections/{collection_name}/documents",
                    json={"doc_id": doc_id, "document": document}
                )

            return True

        except Exception as e:
            print(f"Error saving feature to MemoBase: {e}")
            return False

    async def _get_feature_async(self, user_id: str, feature_type: str,
                                  feature_value: str) -> Optional[Dict[str, Any]]:
        """异步获取特征"""
        client = self._get_client()
        if not client:
            return None

        try:
            collection_name = "user_features"
            doc_id = f"feature_{user_id}_{feature_type}_{feature_value}"

            response = await client.get(f"/collections/{collection_name}/documents/{doc_id}")

            if response.status_code == 200:
                data = response.json()
                return data.get("document", {})
            return None

        except Exception:
            return None

    async def save_all_features(self, user_id: str, features: List[Dict[str, Any]]) -> bool:
        """批量保存特征到 MemoBase"""
        client = self._get_client()
        if not client:
            return False

        try:
            collection_name = "user_features"

            for feature in features:
                doc_id = f"feature_{user_id}_{feature.get('feature_type', 'unknown')}_{feature.get('feature_value', 'unknown')}"

                document = {
                    "user_id": user_id,
                    "feature_type": feature.get("feature_type", "unknown"),
                    "feature_value": feature.get("feature_value", ""),
                    "confidence": feature.get("confidence", 0.5),
                    "reasoning": feature.get("reasoning", ""),
                    "evidence": feature.get("evidence", []),
                    "updated_at": self._get_timestamp()
                }

                existing = await self._get_feature_async(
                    user_id, feature.get("feature_type", "unknown"), feature.get("feature_value", "")
                )

                if existing:
                    await client.put(
                        f"/collections/{collection_name}/documents/{doc_id}",
                        json=document
                    )
                else:
                    await client.post(
                        f"/collections/{collection_name}/documents",
                        json={"doc_id": doc_id, "document": document}
                    )

            return True

        except Exception as e:
            print(f"Error saving features to MemoBase: {e}")
            return False

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None


memo_base_service = MemoBaseService()
