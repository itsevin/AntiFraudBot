# -*- coding: utf-8 -*-
"""
AI 智能分析插件 - 鉴诈功能
集成大模型 API 进行诈骗话术识别
"""

from nonebot import on_command, logger, get_plugin_config, require
from nonebot.adapters.onebot.v11 import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg

require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session

from .llm_client import analyze_fraud
from .config import AIConfig

# 获取配置
config = get_plugin_config(AIConfig)

# 注册鉴诈指令
fraud_analysis = on_command(
    "鉴诈",
    aliases={"识骗", "防骗分析"},
    priority=5,
    block=True
)


@fraud_analysis.handle()
async def handle_fraud_analysis(
    bot: Bot,
    event: Event,
    session: async_scoped_session,
    args: Message = CommandArg()
):
    """处理鉴诈指令"""
    # 检查功能开关
    group_id = _get_group_id(event)
    if group_id:
        from src.database.crud import get_group_config
        group_config = await get_group_config(session, group_id)
        if not group_config.ai_analysis:
            await fraud_analysis.finish("⚠️ 本群已关闭 AI 鉴诈功能")

    # 获取待分析文本
    text = args.extract_plain_text().strip()

    if not text:
        await fraud_analysis.finish(
            "📝 使用方法：鉴诈 [待分析内容]\n"
            "例如：鉴诈 您好，我是某某银行客服，您的账户存在异常..."
        )
        return

    # 检查 API 配置
    if not config.ai_api_key:
        await fraud_analysis.finish(
            "⚠️ AI 功能未配置，请联系管理员设置 API Key"
        )
        return

    # 发送分析中提示
    await fraud_analysis.send("🔍 正在分析中，请稍候...")

    analysis_success = False
    result = {}

    try:
        # 调用 AI 分析
        result = await analyze_fraud(
            text=text,
            api_key=config.ai_api_key,
            api_base=config.ai_api_base,
            model=config.ai_model,
            session=session,
            user_id=event.get_user_id(),
            group_id=_get_group_id(event)
        )
        analysis_success = True

    except Exception as e:
        logger.error(f"AI 分析失败: {e}")
        await fraud_analysis.finish(f"❌ 分析失败：{str(e)}")

    if analysis_success:
        # 构建返回消息
        response = _format_result(result)
        await fraud_analysis.finish(response)


def _get_group_id(event: Event) -> str | None:
    """获取群号"""
    session_id = event.get_session_id()
    if '_' in session_id:
        return session_id.split("_")[1]
    return None


def _format_result(result: dict) -> str:
    """格式化分析结果"""
    risk_emoji = {
        "低危": "🟢",
        "中危": "🟡",
        "高危": "🔴"
    }

    emoji = risk_emoji.get(result.get("risk_level", "低危"), "⚪")

    msg = f"""
🔍 【智能鉴诈结果】

{emoji} 风险等级：{result.get('risk_level', '未知')}
📋 诈骗类型：{result.get('fraud_type', '未识别')}

🎭 话术特征：
{result.get('features', '无特殊特征')}

💡 防范建议：
{result.get('advice', '请保持警惕，不轻信陌生信息')}
""".strip()

    return msg
