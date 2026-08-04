# -*- coding: utf-8 -*-
"""
AI 聊天机器人主插件
支持多轮对话、知识库检索、群组数据分析
"""

from nonebot import on_message, on_command, logger, get_plugin_config, require, get_driver
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.rule import to_me
from nonebot.params import EventPlainText
import time

require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session

from .config import ChatbotConfig
from .context_manager import get_context_manager
from .rag_engine import get_rag_engine
from .prompt_builder import PromptBuilder
from .llm_client import LLMClient

from src.database.crud import log_chatbot_conversation, get_group_detection_stats

# 获取配置
config = get_plugin_config(ChatbotConfig)
driver = get_driver()

# 初始化核心组件
context_manager = get_context_manager(
    timeout=config.chatbot_context_timeout,
    max_rounds=config.chatbot_max_context_rounds
)
rag_engine = get_rag_engine()

# LLM 客户端将在运行时初始化
llm_client = None


@driver.on_startup
async def init_llm_client():
    """启动时初始化 LLM 客户端"""
    global llm_client
    try:
        # 从 fraud_ai 插件获取 AI 配置
        from src.plugins.fraud_ai.config import AIConfig
        ai_config = get_plugin_config(AIConfig)

        if ai_config.ai_api_key:
            llm_client = LLMClient(
                api_key=ai_config.ai_api_key,
                api_base=ai_config.ai_api_base,
                model=ai_config.ai_model
            )
            logger.success("AI 聊天机器人初始化成功")
        else:
            logger.warning("AI API Key 未配置，聊天机器人功能将无法使用")
    except Exception as e:
        logger.error(f"初始化 LLM 客户端失败: {e}")


# ==================== 消息处理器 ====================

# 1. 自定义触发规则
async def chatbot_rule(event: Event) -> bool:
    """
    触发规则：
    1. 私聊：始终触发
    2. 群聊：配置开启了@触发 且 确实@了机器人
    """
    if isinstance(event, GroupMessageEvent):
        return config.chatbot_trigger_at_me and event.is_tome()
    # 私聊默认触发
    return True

chatbot_at = on_message(rule=chatbot_rule, priority=10, block=False)

# 2. 命令触发
chatbot_cmd = on_command(
    "反诈咨询",
    aliases=set(config.chatbot_trigger_keywords),
    priority=5,
    block=True
)


@chatbot_at.handle()
async def handle_at_message(
    bot: Bot,
    event: Event,
    session: async_scoped_session,
    message: str = EventPlainText()
):
    """处理 @机器人(群) 或 私聊消息"""
    if not config.chatbot_enabled:
        return

    # 私聊或群聊已在 rule 中过滤，这里无需再判断 trigger_at_me

    user_message = message.strip()
    if not user_message:
        await bot.send(event, "👋 你好！我是反诈卫士，有什么可以帮到你的吗？\n\n💡 你可以问我：\n- 如何识别刷单诈骗？\n- 我收到一条可疑短信...\n- 什么是杀猪盘？")
        return

    await _process_chatbot(bot, event, session, user_message)


@chatbot_cmd.handle()
async def handle_command(
    bot: Bot,
    event: Event,
    session: async_scoped_session,
    message: str = EventPlainText()
):
    """处理命令触发"""
    if not config.chatbot_enabled:
        await chatbot_cmd.finish("⚠️ 聊天功能暂未开启")
        return

    user_message = message.strip()
    if not user_message:
        await chatbot_cmd.send("👋 你好！我是反诈卫士，有什么可以帮到你的吗？\n\n💡 你可以问我：\n- 如何识别刷单诈骗？\n- 我收到一条可疑短信...\n- 什么是杀猪盘？")
        return

    await _process_chatbot(bot, event, session, user_message)


async def _process_chatbot(
    bot: Bot,
    event: Event,
    session,
    user_message: str
):
    """
    核心处理逻辑

    Args:
        bot: Bot 实例
        event: 事件
        session: 数据库会话
        user_message: 用户消息
    """
    # 检查 LLM 客户端
    if llm_client is None:
        await bot.send(event, "⚠️ AI 功能未配置，请联系管理员设置 API Key")
        return

    user_id = event.get_user_id()
    group_id = _get_group_id(event)

    # 发送处理中提示
    # await bot.send(event, "🤔 正在思考...")

    start_time = time.time()

    try:
        # 1. 获取对话上下文
        context_history = await context_manager.get_context(user_id, group_id)
        logger.debug(f"用户 {user_id} 上下文轮数: {len(context_history) // 2}")

        # 2. RAG 检索
        rag_results = []
        if config.chatbot_rag_enabled:
            rag_results = await rag_engine.search(user_message, config.chatbot_rag_top_k)
            logger.debug(f"RAG 检索到 {len(rag_results)} 条结果")

        # 3. 获取群组数据
        group_stats = None
        if config.chatbot_use_group_stats and group_id:
            group_stats = await get_group_detection_stats(session, group_id, days=30)
            logger.debug(f"群组统计: {group_stats}")

        # 4. 构建提示词
        prompt = PromptBuilder.build_chatbot_prompt(
            user_question=user_message,
            context_history=context_history,
            rag_results=rag_results,
            group_stats=group_stats
        )

        # 5. 调用大模型
        bot_response = await llm_client.chat(
            messages=prompt["messages"],
            temperature=0.7,
            max_tokens=500
        )

        # 6. 更新上下文
        await context_manager.add_message(user_id, group_id, "user", user_message)
        await context_manager.add_message(user_id, group_id, "assistant", bot_response)

        # 7. 记录日志
        response_time = int((time.time() - start_time) * 1000)
        await log_chatbot_conversation(
            session=session,
            user_id=user_id,
            group_id=group_id,
            user_message=user_message,
            bot_response=bot_response,
            model_used=llm_client.model,
            response_time=response_time,
            rag_context=str(rag_results) if rag_results else None
        )

        logger.info(f"聊天机器人响应成功 - 用户: {user_id}, 耗时: {response_time}ms")

        # 8. 发送回复
        await bot.send(event, bot_response)

    except Exception as e:
        logger.error(f"聊天机器人处理失败: {e}", exc_info=True)
        await bot.send(event, f"❌ 抱歉，处理出错了：{str(e)}\n\n💡 建议：如遇可疑情况请拨打 96110 反诈专线")


def _get_group_id(event: Event) -> str | None:
    """获取群号"""
    if isinstance(event, GroupMessageEvent):
        return str(event.group_id)
    return None


# ==================== 管理命令 ====================

clear_context_cmd = on_command(
    "清除对话",
    aliases={"重置对话", "清空上下文"},
    priority=5,
    block=True
)


@clear_context_cmd.handle()
async def handle_clear_context(bot: Bot, event: Event):
    """清除对话上下文"""
    user_id = event.get_user_id()
    group_id = _get_group_id(event)

    await context_manager.clear_context(user_id, group_id)
    await clear_context_cmd.finish("✅ 对话历史已清除，我们可以重新开始聊天了！")


context_stats_cmd = on_command(
    "对话统计",
    priority=5,
    block=True
)


@context_stats_cmd.handle()
async def handle_context_stats(bot: Bot, event: Event):
    """查看对话统计"""
    stats = await context_manager.get_stats()
    msg = f"""📊 对话统计

活跃对话数: {stats['active_contexts']}
总消息数: {stats['total_messages']}
"""
    await context_stats_cmd.finish(msg)


# ==================== 定时任务 ====================

from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("interval", minutes=5, id="cleanup_chatbot_context")
async def cleanup_expired_contexts():
    """每5分钟清理一次过期上下文"""
    try:
        count = await context_manager.cleanup_expired()
        if count > 0:
            logger.info(f"清理了 {count} 个过期的对话上下文")
    except Exception as e:
        logger.error(f"清理对话上下文失败: {e}")


# ==================== 插件元信息 ====================

__plugin_meta__ = {
    "name": "AI聊天机器人",
    "description": "智能反诈对话助手，支持多轮对话、知识库检索",
    "usage": """
使用方法：
@机器人 [问题] (支持多轮对话)

示例：
- @机器人 如何识别刷单诈骗？
- @机器人 我收到一条可疑短信...
- @机器人 什么是杀猪盘？

管理命令：
- 清除对话 - 清除对话历史
- 对话统计 - 查看统计信息
""",
    "version": "1.0.0"
}
