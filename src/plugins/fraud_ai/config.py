# -*- coding: utf-8 -*-
"""
AI 配置项
"""

from pydantic import BaseModel
from typing import Optional


class AIConfig(BaseModel):
    """AI 智能分析配置"""

    # API 密钥 (必填)
    ai_api_key: Optional[str] = None

    # API 基础地址 (支持 DeepSeek、通义千问、OpenAI 等)
    ai_api_base: str = "https://api.deepseek.com/v1"

    # 模型名称
    ai_model: str = "deepseek-chat"

    # 请求超时时间 (秒)
    ai_timeout: int = 30

    # 最大 Token 数
    ai_max_tokens: int = 1000
