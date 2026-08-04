# -*- coding: utf-8 -*-
"""
数据库 CRUD 操作封装
提供常用的增删改查方法
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from nonebot_plugin_orm import async_scoped_session
from sqlalchemy import select, func, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Keyword,
    DetectionLog,
    UserScore,
    QuizQuestion,
    GroupConfig,
    AIAnalysisLog,
    ConversationContext,
    ChatbotLog,
    UserConfig
)


# ==================== 敏感词操作 ====================

async def get_all_keywords(session: AsyncSession) -> List[Keyword]:
    """获取所有启用的敏感词"""
    result = await session.execute(
        select(Keyword).where(Keyword.is_active == True)
    )
    return result.scalars().all()


async def get_keyword_set(session: AsyncSession) -> set:
    """获取敏感词集合，用于快速匹配"""
    keywords = await get_all_keywords(session)
    return {kw.word for kw in keywords}


async def add_keyword(
    session: AsyncSession,
    word: str,
    category: str = "通用",
    risk_level: int = 1
) -> Tuple[bool, str]:
    """添加敏感词"""
    # 检查是否已存在
    result = await session.execute(
        select(Keyword).where(Keyword.word == word)
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.is_active:
            return False, f"敏感词 '{word}' 已存在"
        else:
            # 重新启用已禁用的敏感词
            existing.is_active = True
            existing.category = category
            existing.risk_level = risk_level
            await session.commit()
            return True, f"敏感词 '{word}' 已重新启用"

    new_keyword = Keyword(
        word=word,
        category=category,
        risk_level=risk_level
    )
    session.add(new_keyword)
    await session.commit()
    return True, f"成功添加敏感词：{word}"


async def remove_keyword(session: AsyncSession, word: str) -> Tuple[bool, str]:
    """删除敏感词（软删除）"""
    result = await session.execute(
        select(Keyword).where(Keyword.word == word)
    )
    keyword = result.scalar_one_or_none()
    if not keyword:
        return False, f"敏感词 '{word}' 不存在"

    keyword.is_active = False
    await session.commit()
    return True, f"成功删除敏感词：{word}"


# ==================== 拦截日志操作 ====================

async def log_detection(
    session: AsyncSession,
    user_id: str,
    keyword: str,
    message_content: str,
    group_id: Optional[str] = None,
    risk_level: int = 1,
    saved_value_estimate: int = 0
) -> DetectionLog:
    """记录一次拦截日志"""
    log = DetectionLog(
        group_id=group_id,
        user_id=user_id,
        keyword=keyword,
        message_content=message_content[:500],  # 限制长度
        risk_level=risk_level,
        saved_value_estimate=saved_value_estimate
    )
    session.add(log)
    await session.commit()
    return log


async def get_detection_stats(session: AsyncSession) -> dict:
    """获取拦截统计数据"""
    # 总拦截次数
    total_result = await session.execute(select(func.count(DetectionLog.id)))
    total_count = total_result.scalar() or 0

    # 今日拦截次数
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await session.execute(
        select(func.count(DetectionLog.id)).where(
            DetectionLog.detected_at >= today_start
        )
    )
    today_count = today_result.scalar() or 0

    # 近7天拦截趋势
    week_ago = datetime.now() - timedelta(days=7)
    trend_result = await session.execute(
        select(
            func.date(DetectionLog.detected_at).label('date'),
            func.count(DetectionLog.id).label('count')
        ).where(
            DetectionLog.detected_at >= week_ago
        ).group_by(
            func.date(DetectionLog.detected_at)
        ).order_by('date')
    )
    trend_data = [{"date": str(row.date), "count": row.count} for row in trend_result]

    # 诈骗类型分布（按关键词分类）
    return {
        "total_count": total_count,
        "today_count": today_count,
        "trend_data": trend_data
    }


async def get_top_keywords(session: AsyncSession, limit: int = 5) -> List[dict]:
    """获取命中次数最多的关键词"""
    result = await session.execute(
        select(
            DetectionLog.keyword,
            func.count(DetectionLog.id).label('count')
        ).group_by(DetectionLog.keyword).order_by(desc('count')).limit(limit)
    )
    return [{"keyword": row.keyword, "count": row.count} for row in result]


# ==================== 用户积分操作 ====================

async def get_or_create_user_score(
    session: AsyncSession,
    user_id: str,
    group_id: Optional[str] = None
) -> UserScore:
    """获取或创建用户积分记录"""
    query = select(UserScore).where(UserScore.user_id == user_id)
    if group_id:
        query = query.where(UserScore.group_id == group_id)
    else:
        # 显式匹配 group_id 为 NULL 的记录
        query = query.where(UserScore.group_id.is_(None))

    # 使用 scalars().first() 避免多条记录报错
    result = await session.execute(query)
    user_score = result.scalars().first()

    if not user_score:
        user_score = UserScore(user_id=user_id, group_id=group_id)
        session.add(user_score)
        await session.commit()
        await session.refresh(user_score)

    return user_score


async def add_score(
    session: AsyncSession,
    user_id: str,
    points: int,
    group_id: Optional[str] = None
) -> UserScore:
    """增加用户积分"""
    user_score = await get_or_create_user_score(session, user_id, group_id)
    user_score.score += points
    await session.commit()
    return user_score


async def sign_in(
    session: AsyncSession,
    user_id: str,
    group_id: Optional[str] = None
) -> Tuple[bool, str, int]:
    """用户签到"""
    user_score = await get_or_create_user_score(session, user_id, group_id)

    today = datetime.now().date()
    if user_score.last_sign_in and user_score.last_sign_in.date() == today:
        return False, "今天已经签到过了", user_score.score

    user_score.last_sign_in = datetime.now()
    user_score.sign_in_days += 1
    user_score.score += 5  # 签到奖励5分
    await session.commit()
    await session.refresh(user_score)

    return True, f"签到成功！连续签到 {user_score.sign_in_days} 天，获得 5 积分", user_score.score


async def get_leaderboard(
    session: AsyncSession,
    group_id: Optional[str] = None,
    limit: int = 10
) -> List[UserScore]:
    """获取积分排行榜"""
    query = select(UserScore).order_by(desc(UserScore.score)).limit(limit)
    if group_id:
        query = query.where(UserScore.group_id == group_id)

    result = await session.execute(query)
    return result.scalars().all()


# ==================== 题库操作 ====================

async def get_random_questions(
    session: AsyncSession,
    count: int = 3
) -> List[QuizQuestion]:
    """随机获取题目"""
    result = await session.execute(
        select(QuizQuestion)
        .where(QuizQuestion.is_active == True)
        .order_by(func.random())
        .limit(count)
    )
    return result.scalars().all()


async def get_question_count(session: AsyncSession) -> int:
    """获取题库题目数量"""
    result = await session.execute(
        select(func.count(QuizQuestion.id)).where(QuizQuestion.is_active == True)
    )
    return result.scalar() or 0


# ==================== 群配置操作 ====================

async def get_group_config(
    session: AsyncSession,
    group_id: str
) -> GroupConfig:
    """获取群配置，不存在则创建默认配置"""
    result = await session.execute(
        select(GroupConfig).where(GroupConfig.group_id == group_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = GroupConfig(group_id=group_id)
        session.add(config)
        await session.commit()
        await session.refresh(config)

    return config


async def update_group_config(
    session: AsyncSession,
    group_id: str,
    **kwargs
) -> GroupConfig:
    """更新群配置"""
    config = await get_group_config(session, group_id)
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    await session.commit()
    return config


# ==================== AI分析日志操作 ====================

async def log_ai_analysis(
    session: AsyncSession,
    user_id: str,
    input_text: str,
    risk_level: str,
    fraud_type: Optional[str],
    analysis_result: str,
    model_used: str,
    group_id: Optional[str] = None,
    reasoning_trace: Optional[str] = None
) -> AIAnalysisLog:
    """记录AI分析日志"""
    log = AIAnalysisLog(
        group_id=group_id,
        user_id=user_id,
        input_text=input_text[:1000],
        risk_level=risk_level,
        fraud_type=fraud_type,
        analysis_result=analysis_result,
        reasoning_trace=reasoning_trace,
        model_used=model_used
    )
    session.add(log)
    await session.commit()
    return log


async def get_ai_analysis_stats(session: AsyncSession) -> dict:
    """获取AI分析统计"""
    # 总分析次数
    total_result = await session.execute(select(func.count(AIAnalysisLog.id)))
    total_count = total_result.scalar() or 0

    # 高危检测次数
    high_risk_result = await session.execute(
        select(func.count(AIAnalysisLog.id)).where(AIAnalysisLog.risk_level == "高危")
    )
    high_risk_count = high_risk_result.scalar() or 0

    return {
        "total_count": total_count,
        "high_risk_count": high_risk_count
    }


# ==================== 聊天机器人操作 ====================

async def log_chatbot_conversation(
    session: AsyncSession,
    user_id: str,
    user_message: str,
    bot_response: str,
    model_used: str,
    response_time: int,
    group_id: Optional[str] = None,
    rag_context: Optional[str] = None
) -> ChatbotLog:
    """记录聊天机器人对话日志"""
    log = ChatbotLog(
        user_id=user_id,
        group_id=group_id,
        user_message=user_message[:1000],  # 限制长度
        bot_response=bot_response[:2000],
        rag_context=rag_context[:1000] if rag_context else None,
        model_used=model_used,
        response_time=response_time
    )
    session.add(log)
    await session.commit()
    return log


async def get_group_detection_stats(
    session: AsyncSession,
    group_id: Optional[str],
    days: int = 30
) -> dict:
    """获取群组拦截统计数据（用于聊天机器人上下文）"""
    if not group_id:
        return {
            "total_count": 0,
            "top_types": [],
            "avg_score": 0
        }

    # 计算起始日期
    start_date = datetime.now() - timedelta(days=days)

    # 查询拦截次数
    count_result = await session.execute(
        select(func.count(DetectionLog.id))
        .where(DetectionLog.group_id == group_id)
        .where(DetectionLog.detected_at >= start_date)
    )
    total_count = count_result.scalar() or 0

    # 查询高发诈骗类型（从AI分析日志）
    type_result = await session.execute(
        select(AIAnalysisLog.fraud_type, func.count(AIAnalysisLog.id).label('count'))
        .where(AIAnalysisLog.group_id == group_id)
        .where(AIAnalysisLog.analyzed_at >= start_date)
        .where(AIAnalysisLog.fraud_type.isnot(None))
        .where(AIAnalysisLog.fraud_type != "非诈骗信息")
        .group_by(AIAnalysisLog.fraud_type)
        .order_by(desc('count'))
        .limit(3)
    )
    top_types = [row[0] for row in type_result.all()]

    # 计算群成员平均积分（粗略估算反诈意识）
    score_result = await session.execute(
        select(func.avg(UserScore.score))
        .where(UserScore.group_id == group_id)
    )
    avg_score_raw = score_result.scalar() or 0
    # 转换为百分制评分
    avg_score = min(int(avg_score_raw / 10), 100)

    return {
        "total_count": total_count,
        "top_types": top_types,
        "avg_score": avg_score if avg_score > 0 else 60  # 默认60分
    }


async def cleanup_expired_contexts(session: AsyncSession) -> int:
    """清理过期的对话上下文（由定时任务调用）"""
    result = await session.execute(
        select(ConversationContext).where(
            ConversationContext.expires_at < datetime.now()
        )
    )
    expired = result.scalars().all()

    for ctx in expired:
        await session.delete(ctx)

    await session.commit()
    return len(expired)


# ==================== 用户配置操作 ====================

async def get_user_config(session: AsyncSession, user_id: str) -> UserConfig:
    """获取用户配置，不存在则创建默认配置"""
    result = await session.execute(
        select(UserConfig).where(UserConfig.user_id == user_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = UserConfig(user_id=user_id)
        session.add(config)
        await session.commit()
        await session.refresh(config)

    return config


async def update_user_config(session: AsyncSession, user_id: str, **kwargs) -> UserConfig:
    """更新用户配置"""
    config = await get_user_config(session, user_id)

    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    await session.commit()
    await session.refresh(config)
    return config
