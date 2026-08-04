from datetime import datetime, timedelta
import random
import hashlib
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_

from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session

# 使用相对导入避免路径问题
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.database.models import (
    DetectionLog,
    UserScore,
    GroupConfig,
    AIAnalysisLog,
    ChatbotLog,
    DailyBriefing
)
from src.web.security import mask_identifier

router = APIRouter()

async def get_db():
    async with get_session() as session:
        yield session

# ==================== 核心指标接口 ====================

@router.get("/impact_stats")
async def get_impact_stats(session: AsyncSession = Depends(get_db)):
    """
    获取影响力统计 (风险防护指数 & 算力消耗)
    """
    # 风险防护指数 (基于风险等级加权: 高危*50, 中危*20, 低危*5)
    # 改用风险等级求和，比"挽回损失"更客观
    protection_score = await session.execute(
        select(func.sum(DetectionLog.risk_level * 10))  # 每个风险等级 * 10
    )
    total_protection = protection_score.scalar() or 0

    # 累计 Token 消耗
    token_usage = await session.execute(
        select(func.sum(ChatbotLog.token_usage))
    )
    total_tokens = token_usage.scalar() or 0

    # 拦截总数
    detection_count = await session.execute(
        select(func.count(DetectionLog.id))
    )
    total_detections = detection_count.scalar() or 0

    return {
        "total_protection_score": total_protection,  # 改名
        "total_tokens_used": total_tokens,
        "total_detections": total_detections
    }

@router.get("/defense_index")
async def get_defense_index(session: AsyncSession = Depends(get_db)):
    """
    获取防御准备度指数 (DRI)
    模拟计算：基础分(60) + 活跃度修正 + 响应速度修正
    """
    # 获取平均 AI 响应延迟
    latency_query = await session.execute(
        select(func.avg(ChatbotLog.latency_ms)).where(ChatbotLog.latency_ms > 0)
    )
    avg_latency = latency_query.scalar() or 0

    # 时延得分 (越快分越高，基准 2000ms)
    # <500ms: 30分, >4000ms: 0分
    latency_score = max(0, min(30, 30 * (1 - avg_latency / 4000))) if avg_latency else 25 # 默认给个不错的分数

    # 活跃群组覆盖率 (此处简化为 活跃群组数/总群组数，若无总数则给默认值)
    active_groups = await session.execute(select(func.count(GroupConfig.id)))
    group_activation_score = min(40, (active_groups.scalar() or 0) * 2) # 假设每个群+2分，上限40

    # 基础运行分 (假设系统正常运行)
    base_score = 60

    # 无需随机微扰动，保持真实
    dri_score = min(100, max(0, base_score + latency_score + group_activation_score))

    return {
        "dri_score": round(dri_score, 1),
        "components": {
            "latency_score": round(latency_score, 1),
            "coverage_score": round(group_activation_score, 1),
            "system_health": base_score
        }
    }

@router.get("/geo_table")
async def get_geo_map(session: AsyncSession = Depends(get_db)):
    """
    赛博威胁地图数据
    基于 Group ID 哈希生成的虚拟坐标
    """
    # 获取活跃的群组配置
    groups = await session.execute(select(GroupConfig))
    group_list = groups.scalars().all()

    # 获取最近24小时有拦截记录的群组ID
    last_24h = datetime.now() - timedelta(hours=24)
    recent_attacks = await session.execute(
        select(DetectionLog.group_id)
        .where(DetectionLog.detected_at >= last_24h)
        .distinct()
    )
    attacked_group_ids = set(recent_attacks.scalars().all())

    geo_points = []

    for group in group_list:
        # 如果数据库还没存坐标，就根据群号生成一个固定的
        # 中国大陆范围: Lat 22-45, Lng 100-122 (主要人口密集区)
        if not group.geo_location:
            # 简单的哈希映射
            h = hashlib.md5(str(group.group_id).encode()).hexdigest()
            lat = 22 + (int(h[0:4], 16) % 2300) / 100  # 22-45
            lng = 100 + (int(h[4:8], 16) % 2200) / 100  # 100-122
            loc_str = f"{lat},{lng}"
        else:
            loc_str = group.geo_location

        lat, lng = map(float, loc_str.split(","))

        # 状态：是否有最近的拦截记录
        is_attacked = group.group_id in attacked_group_ids

        geo_points.append({
            "name": f"Group {str(group.group_id)[-4:]}",
            "value": [lng, lat, 100 if is_attacked else 10], # value[2] 为热度
            "group_id": mask_identifier(group.group_id),
            "status": "alert" if is_attacked else "secure"
        })

    return {"points": geo_points}

@router.get("/ai/live_stream")
async def get_ai_stream(
    limit: int = Query(default=10, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    """
    获取 AI 战术情报官实时流
    """
    logs = await session.execute(
        select(AIAnalysisLog).order_by(AIAnalysisLog.analyzed_at.desc()).limit(limit)
    )

    stream_data = []
    for log in logs.scalars():
        stream_data.append({
            "id": log.id,
            "time": log.analyzed_at.strftime("%H:%M:%S"),
            "risk": log.risk_level,
            "type": log.fraud_type,
            # 如果没有 reasoning_trace，就用 analysis_result 的前一段作为模拟
            "trace": log.reasoning_trace or (log.analysis_result[:50] + "...")
        })

    return {"stream": stream_data}

@router.get("/ai/daily_report")
async def get_daily_report(session: AsyncSession = Depends(get_db)):
    """
    获取今日安全研判日报
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    report = await session.execute(
        select(DailyBriefing).where(DailyBriefing.report_date == today)
    )
    report_obj = report.scalar_one_or_none()

    if report_obj:
        return {"content": report_obj.content, "generated_at": report_obj.generated_at}
    else:
        # 默认展示“近7天全网态势”分析 (Volume preferred)
        now = datetime.now()
        start_7d = now - timedelta(days=7)

        det_count = (await session.execute(
            select(func.count(DetectionLog.id)).where(DetectionLog.detected_at >= start_7d)
        )).scalar() or 0

        # 风险防护指数 (替代原来的挽回损失)
        protection_score = (await session.execute(
            select(func.sum(DetectionLog.risk_level * 10)).where(DetectionLog.detected_at >= start_7d)
        )).scalar() or 0

        ai_count = (await session.execute(
            select(func.count(AIAnalysisLog.id)).where(AIAnalysisLog.analyzed_at >= start_7d)
        )).scalar() or 0

        template_report = f"""# {now.strftime('%Y年%m月')} 反诈防御态势周报

## 📡 态势概览 (近7日)
本周系统持续运行，实时监控多变诈骗手法，为群组提供全天候防护。

## 📊 核心指标
| 指标 | 数值 |
|------|------|
| 🚨 威胁拦截 | **{det_count}** 次 |
| 🛡️ 防护指数 | **{protection_score}** 分 |
| 🤖 AI 深度研判 | **{ai_count}** 次 |

## 🎯 防护指数说明
防护指数基于每次拦截的风险等级加权计算：
- 高危威胁 (等级5) = 50 分
- 中危 (等级3-4) = 30-40 分
- 低危 (等级1-2) = 10-20 分

## 💡 防护建议
保持警惕，对涉及资金、个人信息的消息提高甄别意识。

*(详细日报将于每晚 23:55 由 AI 自动生成)*
"""
        return {"content": template_report, "generated_at": None}

@router.get("/forecast")
async def get_forecast(session: AsyncSession = Depends(get_db)):
    """
    获取未来 24h 攻击趋势预测 (基于当前时间种子的稳定预测)
    """
    now = datetime.now()
    # 使用当前小时作为种子，保证一小时内预测曲线不跳变
    seed_key = now.strftime("%Y%m%d%H")
    random.seed(seed_key)

    forecast_data = []

    for i in range(24):
        time_point = now + timedelta(hours=i)
        import math
        hour = time_point.hour
        # 假设晚上 20-24 点是高峰
        base_threat = 5 + 3 * math.sin((hour - 18) * 3.14 / 12)
        # 降低随机波动幅度
        predicted = max(0, base_threat + random.uniform(-0.5, 0.5))

        forecast_data.append({
            "time": time_point.strftime("%H:00"),
            "value": round(predicted, 1)
        })

    # 恢复随机种子
    random.seed()

    return {"forecast": forecast_data}
