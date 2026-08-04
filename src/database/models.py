# -*- coding: utf-8 -*-
"""
数据模型定义
使用 SQLAlchemy ORM + nonebot-plugin-orm
"""

from datetime import datetime
from typing import Optional

from nonebot_plugin_orm import Model
from sqlalchemy import String, Text, Integer, DateTime, Boolean, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column


class Keyword(Model):
    """
    敏感词表
    存储需要检测的敏感词及其分类
    """
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="敏感词")
    category: Mapped[str] = mapped_column(String(50), default="通用", comment="诈骗类型分类")
    risk_level: Mapped[int] = mapped_column(Integer, default=1, comment="风险等级 1-5")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")


class DetectionLog(Model):
    """
    拦截日志表
    记录每次敏感词检测命中的详情
    """
    __tablename__ = "detection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="群号")
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户QQ号")
    keyword: Mapped[str] = mapped_column(String(100), nullable=False, comment="命中的关键词")
    message_content: Mapped[str] = mapped_column(Text, nullable=False, comment="原始消息内容")
    risk_level: Mapped[int] = mapped_column(Integer, default=1, comment="风险等级")
    saved_value_estimate: Mapped[int] = mapped_column(Integer, default=0, comment="预估挽回损失(元)")
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="检测时间")


class UserScore(Model):
    """
    用户积分表
    记录用户的反诈答题积分
    """
    __tablename__ = "user_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户QQ号")
    group_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="群号")
    score: Mapped[int] = mapped_column(Integer, default=0, comment="累计积分")
    quiz_count: Mapped[int] = mapped_column(Integer, default=0, comment="答题次数")
    correct_count: Mapped[int] = mapped_column(Integer, default=0, comment="正确次数")
    sign_in_days: Mapped[int] = mapped_column(Integer, default=0, comment="累计签到天数")
    last_sign_in: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="最后签到时间")
    last_quiz: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, comment="最后答题时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="首次记录时间")


class QuizQuestion(Model):
    """
    题库表
    存储反诈知识问答题目
    """
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, comment="诈骗类型分类")
    question: Mapped[str] = mapped_column(Text, nullable=False, comment="题目内容")
    options: Mapped[str] = mapped_column(JSON, nullable=False, comment="选项列表 JSON")
    answer: Mapped[str] = mapped_column(String(10), nullable=False, comment="正确答案 A/B/C/D")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, comment="答案解析")
    difficulty: Mapped[int] = mapped_column(Integer, default=1, comment="难度等级 1-3")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")


class GroupConfig(Model):
    """
    群配置表
    存储各群的功能开关配置
    """
    __tablename__ = "group_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="群号")
    keyword_detection: Mapped[bool] = mapped_column(Boolean, default=True, comment="关键词检测开关")
    url_detection: Mapped[bool] = mapped_column(Boolean, default=True, comment="URL检测开关")
    ai_analysis: Mapped[bool] = mapped_column(Boolean, default=True, comment="AI分析开关")
    quiz_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="答题功能开关")
    knowledge_push: Mapped[bool] = mapped_column(Boolean, default=True, comment="知识推送开关")
    example_push: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, nullable=True, comment="案例推送开关")
    geo_location: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="虚拟地理坐标(lat,lng)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")


class AIAnalysisLog(Model):
    """
    AI分析日志表
    记录每次AI鉴诈的结果
    """
    __tablename__ = "ai_analysis_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="群号")
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="请求用户QQ号")
    input_text: Mapped[str] = mapped_column(Text, nullable=False, comment="输入的待分析文本")
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, comment="风险等级: 低危/中危/高危")
    fraud_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="诈骗类型")
    analysis_result: Mapped[str] = mapped_column(Text, nullable=False, comment="AI分析结果全文")
    reasoning_trace: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="AI思维链日志")
    model_used: Mapped[str] = mapped_column(String(50), nullable=False, comment="使用的AI模型")
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="分析时间")


class ConversationContext(Model):
    """
    对话上下文表
    存储用户的对话历史，支持多轮对话
    """
    __tablename__ = "conversation_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户QQ号", index=True)
    group_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="群号", index=True)
    context: Mapped[str] = mapped_column(JSON, nullable=False, comment="对话历史（JSON数组）")
    message_count: Mapped[int] = mapped_column(Integer, default=0, comment="消息轮数")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="最后活动时间")
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment="过期时间", index=True)


class ChatbotLog(Model):
    """
    聊天机器人日志表
    记录每次对话的详细信息
    """
    __tablename__ = "chatbot_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, comment="用户QQ号")
    group_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="群号")
    user_message: Mapped[str] = mapped_column(Text, nullable=False, comment="用户消息")
    bot_response: Mapped[str] = mapped_column(Text, nullable=False, comment="机器人回复")
    rag_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="RAG检索内容")
    model_used: Mapped[str] = mapped_column(String(50), nullable=False, comment="使用的模型")
    response_time: Mapped[int] = mapped_column(Integer, nullable=False, comment="响应时间(ms)")
    # 新增高级统计字段
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, comment="AI响应耗时(ms)")
    token_usage: Mapped[int] = mapped_column(Integer, default=0, comment="Token消耗量")
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0, comment="用户情绪评分(-1.0~1.0)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")


class DailyBriefing(Model):
    """
    每日安全简报表
    存储AI生成的每日态势分析
    """
    __tablename__ = "daily_briefings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, unique=True, comment="简报日期")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="简报内容(Markdown)")
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="生成时间")


class UserConfig(Model):
    """
    用户配置表
    存储私聊用户的功能开关配置
    """
    __tablename__ = "user_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True, comment="用户QQ号")
    knowledge_push: Mapped[bool] = mapped_column(Boolean, default=True, comment="知识推送开关")
    example_push: Mapped[bool] = mapped_column(Boolean, default=True, comment="案例推送开关")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")
