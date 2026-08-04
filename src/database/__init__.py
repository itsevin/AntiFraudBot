# -*- coding: utf-8 -*-
"""
数据库模块
使用 nonebot-plugin-orm 官方插件
"""

from .models import Keyword, DetectionLog, UserScore, QuizQuestion, GroupConfig

__all__ = [
    "Keyword",
    "DetectionLog",
    "UserScore",
    "QuizQuestion",
    "GroupConfig",
]
