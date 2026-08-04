# -*- coding: utf-8 -*-
"""
统计数据 API
提供数据大屏所需的各项统计数据
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query

from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import DetectionLog, UserScore, QuizQuestion, AIAnalysisLog
from src.web.security import mask_identifier

router = APIRouter()


async def get_db():
    """获取数据库会话"""
    async with get_session() as session:
        yield session


@router.get("/overview")
async def get_overview(session: AsyncSession = Depends(get_db)):
    """获取总览数据"""
    # 累计拦截次数
    detection_count = await session.execute(
        select(func.count(DetectionLog.id))
    )
    total_detections = detection_count.scalar() or 0

    # 今日拦截
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = await session.execute(
        select(func.count(DetectionLog.id)).where(
            DetectionLog.detected_at >= today
        )
    )
    today_detections = today_count.scalar() or 0

    # 保护用户数（参与答题的用户）
    user_count = await session.execute(
        select(func.count(func.distinct(UserScore.user_id)))
    )
    protected_users = user_count.scalar() or 0

    # AI 分析次数
    ai_count = await session.execute(
        select(func.count(AIAnalysisLog.id))
    )
    ai_analyses = ai_count.scalar() or 0

    # 题库题目数
    quiz_count = await session.execute(
        select(func.count(QuizQuestion.id)).where(QuizQuestion.is_active == True)
    )
    total_questions = quiz_count.scalar() or 0

    # 系统运行天数（假设从第一条日志开始）
    first_log = await session.execute(
        select(DetectionLog.detected_at).order_by(DetectionLog.detected_at).limit(1)
    )
    first_date = first_log.scalar()
    running_days = (datetime.now() - first_date).days + 1 if first_date else 1

    return {
        "total_detections": total_detections,
        "today_detections": today_detections,
        "protected_users": protected_users,
        "ai_analyses": ai_analyses,
        "total_questions": total_questions,
        "running_days": running_days
    }


@router.get("/trend")
async def get_trend(
    days: int = Query(default=7, ge=1, le=365),
    session: AsyncSession = Depends(get_db),
):
    """获取拦截趋势数据"""
    start_date = datetime.now() - timedelta(days=days)

    result = await session.execute(
        select(
            func.date(DetectionLog.detected_at).label('date'),
            func.count(DetectionLog.id).label('count')
        ).where(
            DetectionLog.detected_at >= start_date
        ).group_by(
            func.date(DetectionLog.detected_at)
        ).order_by('date')
    )

    trend_data = [
        {"date": str(row.date), "count": row.count}
        for row in result
    ]

    return {"trend": trend_data}


@router.get("/top_keywords")
async def get_top_keywords(
    limit: int = Query(default=10, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """获取高频敏感词"""
    result = await session.execute(
        select(
            DetectionLog.keyword,
            func.count(DetectionLog.id).label('count')
        ).group_by(
            DetectionLog.keyword
        ).order_by(
            func.count(DetectionLog.id).desc()
        ).limit(limit)
    )

    keywords = [
        {"keyword": row.keyword, "count": row.count}
        for row in result
    ]

    return {"keywords": keywords}


@router.get("/fraud_types")
async def get_fraud_types(session: AsyncSession = Depends(get_db)):
    """获取诈骗类型分布（基于 AI 分析日志）"""
    result = await session.execute(
        select(
            AIAnalysisLog.fraud_type,
            func.count(AIAnalysisLog.id).label('count')
        ).where(
            AIAnalysisLog.fraud_type != None
        ).group_by(
            AIAnalysisLog.fraud_type
        ).order_by(
            func.count(AIAnalysisLog.id).desc()
        )
    )

    types = [
        {"type": row.fraud_type, "count": row.count}
        for row in result
    ]

    return {"fraud_types": types}


@router.get("/recent_logs")
async def get_recent_logs(
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """获取最近的拦截日志"""
    result = await session.execute(
        select(DetectionLog).order_by(
            DetectionLog.detected_at.desc()
        ).limit(limit)
    )

    logs = [
        {
            "id": log.id,
            "group_id": mask_identifier(log.group_id),
            "user_id": mask_identifier(log.user_id),
            "keyword": log.keyword,
            "time": log.detected_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for log in result.scalars()
    ]

    return {"logs": logs}
