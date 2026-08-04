# -*- coding: utf-8 -*-
"""
AI 聊天机器人配置
"""

from pydantic import BaseModel, Field
from typing import List


class ChatbotConfig(BaseModel):
    """聊天机器人配置"""

    # 功能开关
    chatbot_enabled: bool = Field(default=True, description="聊天机器人功能开关")

    # 上下文配置
    chatbot_context_timeout: int = Field(default=600, description="上下文超时时间（秒），默认10分钟")
    chatbot_max_context_rounds: int = Field(default=5, description="最大上下文轮数")

    # RAG 配置
    chatbot_rag_enabled: bool = Field(default=True, description="RAG 知识库检索开关")
    chatbot_rag_top_k: int = Field(default=3, description="RAG 检索返回数量")

    # 触发配置
    chatbot_trigger_at_me: bool = Field(default=True, description="@机器人触发开关")
    chatbot_trigger_keywords: List[str] = Field(
        default=["反诈咨询", "AI咨询", "智能客服"],
        description="关键词触发列表"
    )

    # 群组数据配置
    chatbot_use_group_stats: bool = Field(default=True, description="是否使用群组统计数据")
    chatbot_stats_cache_hours: int = Field(default=1, description="统计数据缓存时间（小时）")

    class Config:
        extra = "ignore"
