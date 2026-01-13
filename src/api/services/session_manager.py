"""
会话管理器
职责：管理用户会话、消息历史
存储策略：内存缓存（TTL 30分钟）+ JSON 文件持久化
"""
import json
import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from pathlib import Path

from ..schemas.chat import ChatMessage, ChatHistory

logger = logging.getLogger(__name__)


class SessionManager:
    """会话管理器 - 内存缓存 + 文件持久化"""

    def __init__(
        self,
        storage_dir: str = "./data/chat_history",
        cache_ttl_minutes: int = 30,
        max_history_messages: int = 100
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.max_history_messages = max_history_messages

        # 内存缓存: {session_id: ChatHistory}
        self._cache: Dict[str, ChatHistory] = {}
        self._last_access: Dict[str, datetime] = {}

        logger.info(f"SessionManager initialized with storage_dir={storage_dir}, cache_ttl={cache_ttl_minutes}min, max_messages={max_history_messages}")

    async def add_message(
        self,
        session_id: str,
        message: ChatMessage
    ) -> None:
        """添加消息到会话"""
        history = await self._get_or_create_history(session_id)
        history.messages.append(message)
        history.updated_at = datetime.now()

        # 限制历史长度
        if len(history.messages) > self.max_history_messages:
            history.messages = history.messages[-self.max_history_messages:]
            logger.info(f"Session {session_id}: Trimmed history to {self.max_history_messages} messages")

        # 更新缓存和持久化
        self._cache[session_id] = history
        self._last_access[session_id] = datetime.now()
        await self._persist_history(session_id, history)

        logger.debug(f"Session {session_id}: Message added (total: {len(history.messages)})")

    async def get_messages(
        self,
        session_id: str
    ) -> List[ChatMessage]:
        """获取会话消息列表"""
        history = await self.get_history(session_id)
        return history.messages if history else []

    async def get_history(
        self,
        session_id: str
    ) -> Optional[ChatHistory]:
        """获取完整历史"""
        # 1. 检查缓存
        if session_id in self._cache:
            self._last_access[session_id] = datetime.now()
            logger.debug(f"Session {session_id}: Cache hit")
            return self._cache[session_id]

        # 2. 从文件加载
        logger.debug(f"Session {session_id}: Cache miss, loading from file")
        history = await self._load_history(session_id)
        if history:
            self._cache[session_id] = history
            self._last_access[session_id] = datetime.now()

        return history

    async def clear_history(self, session_id: str) -> None:
        """清空会话历史"""
        # 清除缓存
        if session_id in self._cache:
            del self._cache[session_id]
        if session_id in self._last_access:
            del self._last_access[session_id]

        # 删除文件
        file_path = self._get_file_path(session_id)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Session {session_id}: History cleared (file deleted)")
        else:
            logger.info(f"Session {session_id}: History cleared (no file found)")

    async def _get_or_create_history(
        self,
        session_id: str
    ) -> ChatHistory:
        """获取或创建历史记录"""
        history = await self.get_history(session_id)

        if not history:
            history = ChatHistory(
                session_id=session_id,
                messages=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                model_name="default",
                metadata={}
            )
            logger.info(f"Session {session_id}: Created new history")

        return history

    async def _persist_history(
        self,
        session_id: str,
        history: ChatHistory
    ) -> None:
        """持久化历史到文件"""
        try:
            file_path = self._get_file_path(session_id)

            # 序列化为 JSON
            data = history.model_dump(mode='json')

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Session {session_id}: History persisted to {file_path}")
        except Exception as e:
            logger.error(f"Failed to persist history for session {session_id}: {e}", exc_info=True)

    async def _load_history(
        self,
        session_id: str
    ) -> Optional[ChatHistory]:
        """从文件加载历史"""
        try:
            file_path = self._get_file_path(session_id)

            if not file_path.exists():
                logger.debug(f"Session {session_id}: No history file found")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 反序列化
            history = ChatHistory(**data)
            logger.debug(f"Session {session_id}: History loaded from file (messages: {len(history.messages)})")
            return history

        except Exception as e:
            logger.error(f"Failed to load history for session {session_id}: {e}", exc_info=True)
            return None

    def _get_file_path(self, session_id: str) -> Path:
        """获取会话文件路径"""
        return self.storage_dir / f"{session_id}.json"

    def cleanup_expired_cache(self) -> int:
        """清理过期缓存（定时任务调用）"""
        now = datetime.now()
        expired_sessions = [
            sid for sid, last_access in self._last_access.items()
            if now - last_access > self.cache_ttl
        ]

        for sid in expired_sessions:
            if sid in self._cache:
                del self._cache[sid]
            del self._last_access[sid]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions from cache")

        return len(expired_sessions)

    def get_cache_stats(self) -> Dict[str, int]:
        """获取缓存统计信息"""
        return {
            "cached_sessions": len(self._cache),
            "total_messages": sum(len(h.messages) for h in self._cache.values())
        }


# 全局单例
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取会话管理器单例"""
    global _session_manager
    if _session_manager is None:
        from src.config import settings
        _session_manager = SessionManager(
            storage_dir=getattr(settings, 'chat_history_dir', './data/chat_history'),
            cache_ttl_minutes=getattr(settings, 'chat_session_ttl_minutes', 30),
            max_history_messages=getattr(settings, 'chat_max_history_messages', 100)
        )
    return _session_manager
