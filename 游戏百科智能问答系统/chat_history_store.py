"""Redis 历史会话存储"""
import json
import logging
from typing import Sequence

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict

from config import config

logger = logging.getLogger(__name__)


def get_history(session_id: str) -> "RedisChatHistoryStore":
    """获取指定会话的历史存储实例"""
    return RedisChatHistoryStore(session_id)


class RedisChatHistoryStore(BaseChatMessageHistory):
    """LangChain 兼容的 Redis 会话历史存储"""

    def __init__(self, session_id: str, ttl: int = None):
        self.session_id = session_id
        self.ttl = ttl or config.redis.session_ttl
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            from db_pool import get_redis
            self._redis = get_redis()
        return self._redis

    @property
    def messages(self) -> Sequence[BaseMessage]:
        """读取会话消息列表"""
        try:
            r = self._get_redis()
            if r is None:
                return []
            data = r.get(f"session:{self.session_id}:messages")
            if not data:
                return []
            return messages_from_dict(json.loads(data))
        except Exception as e:
            logger.warning("读取会话历史失败: %s", e)
            return []

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """追加消息到会话"""
        try:
            r = self._get_redis()
            if r is None:
                return
            existing = list(self.messages)
            existing.extend(messages)
            serialized = json.dumps([message_to_dict(m) for m in existing], ensure_ascii=False)
            r.setex(f"session:{self.session_id}:messages", self.ttl, serialized)
        except Exception as e:
            logger.warning("保存会话历史失败: %s", e)

    def clear(self) -> None:
        """清空会话"""
        try:
            r = self._get_redis()
            if r:
                r.delete(f"session:{self.session_id}:messages")
        except Exception as e:
            logger.warning("清除会话历史失败: %s", e)

    @classmethod
    def list_sessions(cls) -> list:
        """列出所有会话 ID"""
        try:
            from db_pool import get_redis
            r = get_redis()
            if r is None:
                return []
            keys = r.keys("session:*:messages")
            sessions = set()
            for k in keys:
                parts = k.split(":")
                if len(parts) >= 2:
                    sessions.add(parts[1])
            return sorted(sessions)
        except Exception as e:
            logger.warning("列出会话失败: %s", e)
            return []
