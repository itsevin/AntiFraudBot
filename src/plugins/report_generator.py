# -*- coding: utf-8 -*-
"""
每日态势研判生成器
定时任务：每天 23:55 自动生成当日安全简报
"""

from datetime import datetime, timedelta
from nonebot import logger, require, get_plugin_config, get_driver
from sqlalchemy import select, func, and_
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session

from src.database.models import DetectionLog, AIAnalysisLog, DailyBriefing, ChatbotLog
from src.plugins.fraud_ai.config import AIConfig
from src.plugins.ai_chatbot.llm_client import LLMClient

# 获取 AI 配置
ai_config = get_plugin_config(AIConfig)

@scheduler.scheduled_job("cron", hour=23, minute=55, id="daily_report_job")
async def generate_daily_report_job():
    """定时任务：生成日报"""
    logger.info("开始生成每日安全研判日报...")
    await generate_report()

async def generate_report(date: datetime = None):
    """
    生成指定日期的日报
    """
    if date is None:
        date = datetime.now()

    start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = date.replace(hour=23, minute=59, second=59, microsecond=999999)

    async with get_session() as session:
        # 1. 收集当日数据

        # 拦截数量
        detection_count = (await session.execute(
            select(func.count(DetectionLog.id)).where(DetectionLog.detected_at.between(start_time, end_time))
        )).scalar() or 0

        # 风险防护指数 (替代原来的挽回损失)
        protection_score = (await session.execute(
            select(func.sum(DetectionLog.risk_level * 10)).where(DetectionLog.detected_at.between(start_time, end_time))
        )).scalar() or 0

        # AI 分析次数
        ai_count = (await session.execute(
            select(func.count(AIAnalysisLog.id)).where(AIAnalysisLog.analyzed_at.between(start_time, end_time))
        )).scalar() or 0

        # 高频诈骗类型
        top_fraud_types = (await session.execute(
            select(AIAnalysisLog.fraud_type, func.count(AIAnalysisLog.id))
            .where(AIAnalysisLog.analyzed_at.between(start_time, end_time))
            .group_by(AIAnalysisLog.fraud_type)
            .order_by(func.count(AIAnalysisLog.id).desc())
            .limit(3)
        )).all()
        fraud_summary = ", ".join([f"{t[0]}({t[1]}起)" for t in top_fraud_types if t[0]])

        # 高频敏感词
        top_keywords = (await session.execute(
            select(DetectionLog.keyword, func.count(DetectionLog.id))
            .where(DetectionLog.detected_at.between(start_time, end_time))
            .group_by(DetectionLog.keyword)
            .order_by(func.count(DetectionLog.id).desc())
            .limit(5)
        )).all()
        keyword_summary = ", ".join([f"{k[0]}" for k in top_keywords])

        # 2. 调用 LLM 生成简报
        if not ai_config.ai_api_key:
            logger.warning("未配置 AI API Key，无法生成智能日报")
            content = f"【系统日报】今日拦截 {detection_count} 次，AI 分析 {ai_count} 次。请配置 API Key 以获取详细研判。"
        else:
            try:
                llm = LLMClient(ai_config.ai_api_key, ai_config.ai_api_base, ai_config.ai_model)

                prompt_messages = [
                    {"role": "system", "content": "你是一名网络安全专家，负责撰写反诈态势研判报告。请基于数据生成一份专业的 Markdown 格式报告，包含：态势综述、威胁分析、高发类型、防护建议。语气专业严肃，字数控制在300字以内。不要提及金额或挽回损失。"},
                    {"role": "user", "content": f"""
时间范围：{start_time.strftime('%Y-%m-%d')}
核心数据：
- 威胁拦截量：{detection_count} 次
- AI 深度研判：{ai_count} 次
- 风险防护指数：{protection_score} 分
- 高发诈骗类型：{fraud_summary or '暂无集中爆发'}
- 高频敏感词：{keyword_summary or '无明显热点'}

请撰写《每日反诈态势简报》，重点分析威胁拦截情况和高发类型特征。
"""}
                ]

                content = await llm.chat(prompt_messages, temperature=0.7)

            except Exception as e:
                logger.error(f"生成日报失败: {e}")
                content = f"生成日报时发生错误: {e}"

        # 3. 保存到数据库
        # 检查是否已存在当日日报
        existing = (await session.execute(
            select(DailyBriefing).where(DailyBriefing.report_date == start_time)
        )).scalar_one_or_none()

        if existing:
            existing.content = content
            existing.generated_at = datetime.now()
        else:
            new_report = DailyBriefing(
                report_date=start_time,
                content=content
            )
            session.add(new_report)

        await session.commit()
        logger.success(f"日报已生成并保存 ({date.strftime('%Y-%m-%d')})")

# 启动时自动检查是否需要补发今日日报（开发调试用）
driver = get_driver()
@driver.on_startup
async def check_today_report():
    # 开发环境下，如果今天还没生成，就生成一份
    # 生产环境通常只在 23:55 生成
    # 为了演示效果，这里稍微延迟一点执行
    import asyncio
    await asyncio.sleep(10)
    await generate_report(datetime.now())
