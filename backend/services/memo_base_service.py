"""
MemoBase 服务 - 用于存储和检索用户画像数据
"""
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

    def _get_client(self):
        if not self._enabled:
            return None

        if self._client is None:
            try:
                from memobase import MemoBaseClient
                self._client = MemoBaseClient(
                    project_url=self._config.project_url,
                    api_key=self._config.api_key
                )
            except ImportError:
                print("Warning: memobase package not installed. Install with: pip install memobase")
                return None
            except Exception as e:
                print(f"Warning: Failed to connect to MemoBase: {e}")
                return None

        return self._client

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

            existing = await self.get_user_profile(user_id)
            if existing:
                client.update_document(
                    collection_name=collection_name,
                    doc_id=doc_id,
                    document=document
                )
            else:
                client.create_document(
                    collection_name=collection_name,
                    doc_id=doc_id,
                    document=document
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

            doc = client.get_document(
                collection_name=collection_name,
                doc_id=doc_id
            )

            if doc:
                return doc.get("document", {})
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

            doc = {
                "user_id": user_id,
                "session_id": session_id,
                "messages": [{"role": role, "content": content, "timestamp": self._get_timestamp()}],
                "updated_at": self._get_timestamp()
            }

            existing = self._get_conversation_sync(user_id, session_id)
            if existing:
                messages = existing.get("messages", [])
                messages.append({"role": role, "content": content, "timestamp": self._get_timestamp()})
                doc["messages"] = messages
                client.update_document(
                    collection_name=collection_name,
                    doc_id=doc_id,
                    document=doc
                )
            else:
                client.create_document(
                    collection_name=collection_name,
                    doc_id=doc_id,
                    document=doc
                )

            return True

        except Exception as e:
            print(f"Error updating conversation in MemoBase: {e}")
            return False

    def _get_conversation_sync(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """同步获取对话历史"""
        client = self._get_client()
        if not client:
            return None

        try:
            collection_name = "conversations"
            doc_id = f"conv_{user_id}_{session_id}"

            doc = client.get_document(
                collection_name=collection_name,
                doc_id=doc_id
            )

            if doc:
                return doc.get("document", {})
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

            results = client.search(
                collection_name=collection_name,
                query=query,
                limit=limit
            )

            return results if results else []

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

            existing = self._get_feature_sync(user_id, feature_type, feature_value)
            if existing:
                if confidence > existing.get("confidence", 0):
                    client.update_document(
                        collection_name=collection_name,
                        doc_id=doc_id,
                        document=document
                    )
            else:
                client.create_document(
                    collection_name=collection_name,
                    doc_id=doc_id,
                    document=document
                )

            return True

        except Exception as e:
            print(f"Error saving feature to MemoBase: {e}")
            return False

    def _get_feature_sync(self, user_id: str, feature_type: str,
                          feature_value: str) -> Optional[Dict[str, Any]]:
        """同步获取特征"""
        client = self._get_client()
        if not client:
            return None

        try:
            collection_name = "user_features"
            doc_id = f"feature_{user_id}_{feature_type}_{feature_value}"

            doc = client.get_document(
                collection_name=collection_name,
                doc_id=doc_id
            )

            if doc:
                return doc.get("document", {})
            return None

        except Exception:
            return None

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def is_enabled(self) -> bool:
        """检查 MemoBase 是否启用"""
        return self._enabled and self._get_client() is not None


memo_base_service = MemoBaseService()
