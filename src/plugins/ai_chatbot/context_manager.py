# -*- coding: utf-8 -*-
"""
对话上下文管理器
负责管理用户的多轮对话历史
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
import asyncio


class ContextManager:
    """对话上下文管理器 - 内存版本"""

    def __init__(self, timeout: int = 600, max_rounds: int = 5):
        """
        初始化上下文管理器

        Args:
            timeout: 上下文超时时间（秒）
            max_rounds: 最大保留轮数
        """
        self.timeout = timeout
        self.max_rounds = max_rounds
        self._contexts: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    def _get_key(self, user_id: str, group_id: Optional[str]) -> str:
        """生成唯一键"""
        return f"{user_id}_{group_id or 'private'}"

    async def get_context(self, user_id: str, group_id: Optional[str]) -> List[dict]:
        """
        获取对话上下文

        Args:
            user_id: 用户ID
            group_id: 群ID

        Returns:
            对话历史列表
        """
        async with self._lock:
            key = self._get_key(user_id, group_id)
            ctx = self._contexts.get(key)

            if not ctx:
                return []

            # 检查是否过期
            if datetime.now() > ctx["expires_at"]:
                del self._contexts[key]
                return []

            return ctx["context"]

    async def add_message(
        self,
        user_id: str,
        group_id: Optional[str],
        role: str,
        content: str
    ):
        """
        添加消息到上下文

        Args:
            user_id: 用户ID
            group_id: 群ID
            role: 角色（user/assistant）
            content: 消息内容
        """
        async with self._lock:
            key = self._get_key(user_id, group_id)

            if key not in self._contexts:
                self._contexts[key] = {
                    "context": [],
                    "created_at": datetime.now(),
                    "last_activity": datetime.now(),
                    "expires_at": datetime.now() + timedelta(seconds=self.timeout)
                }

            ctx = self._contexts[key]
            ctx["context"].append({"role": role, "content": content})

            # 限制上下文长度（只保留最近 N 轮对话）
            # 每轮对话包含 user + assistant 两条消息
            max_messages = self.max_rounds * 2
            if len(ctx["context"]) > max_messages:
                ctx["context"] = ctx["context"][-max_messages:]

            # 更新活动时间和过期时间
            ctx["last_activity"] = datetime.now()
            ctx["expires_at"] = datetime.now() + timedelta(seconds=self.timeout)

    async def clear_context(self, user_id: str, group_id: Optional[str]):
        """
        清除上下文

        Args:
            user_id: 用户ID
            group_id: 群ID
        """
        async with self._lock:
            key = self._get_key(user_id, group_id)
            if key in self._contexts:
                del self._contexts[key]

    async def cleanup_expired(self) -> int:
        """
        清理过期上下文（由定时任务调用）

        Returns:
            清理的上下文数量
        """
        async with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, ctx in self._contexts.items()
                if now > ctx["expires_at"]
            ]
            for key in expired_keys:
                del self._contexts[key]
            return len(expired_keys)

    async def get_stats(self) -> dict:
        """获取统计信息"""
        async with self._lock:
            return {
                "active_contexts": len(self._contexts),
                "total_messages": sum(len(ctx["context"]) for ctx in self._contexts.values())
            }


# 全局单例
_context_manager_instance: Optional[ContextManager] = None


def get_context_manager(timeout: int = 600, max_rounds: int = 5) -> ContextManager:
    """获取上下文管理器单例"""
    global _context_manager_instance
    if _context_manager_instance is None:
        _context_manager_instance = ContextManager(timeout, max_rounds)
    return _context_manager_instance
