# -*- coding: utf-8 -*-
"""
反诈答题积分系统
包含答题、签到、积分查询、排行榜功能
"""

from nonebot import on_command, logger, require
from nonebot.adapters.onebot.v11 import Bot, Event, Message, GroupMessageEvent, PrivateMessageEvent
from nonebot.params import CommandArg

require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session

from src.database.crud import (
    get_or_create_user_score,
    sign_in,
    add_score,
    get_leaderboard,
    get_random_questions
)
from .quiz_handler import start_quiz_session, get_quiz_state


# ==================== 签到功能 ====================
sign_in_cmd = on_command(
    "签到",
    aliases={"打卡", "每日签到"},
    priority=5,
    block=True
)


@sign_in_cmd.handle()
async def handle_sign_in(
    bot: Bot,
    event: Event,
    session: async_scoped_session
):
    """处理签到指令"""
    # 私聊不支持签到
    if isinstance(event, PrivateMessageEvent):
        await sign_in_cmd.finish("签到功能仅在群聊中可用，请在群内发送 '签到'")

    user_id = event.get_user_id()
    group_id = _get_group_id(event)

    if group_id:
        from src.database.crud import get_group_config
        config = await get_group_config(session, group_id)
        # 签到功能通常默认开启

    success, message, total_score = await sign_in(session, user_id, group_id)

    if success:
        response = f"""
✅ 签到成功！

{message}
💰 当前积分：{total_score} 分
""".strip()
    else:
        response = f"⚠️ {message}\n💰 当前积分：{total_score} 分"

    await sign_in_cmd.finish(response)


# ==================== 积分查询 ====================
my_score_cmd = on_command(
    "我的积分",
    aliases={"积分", "查积分", "积分查询"},
    priority=5,
    block=True
)


@my_score_cmd.handle()
async def handle_my_score(
    bot: Bot,
    event: Event,
    session: async_scoped_session
):
    """查询个人积分"""
    # 私聊不支持积分查询
    if isinstance(event, PrivateMessageEvent):
        await my_score_cmd.finish("积分查询仅在群聊中可用，请在群内发送 '我的积分'")

    user_id = event.get_user_id()
    group_id = _get_group_id(event)

    user_score = await get_or_create_user_score(session, user_id, group_id)

    # 计算正确率
    accuracy = 0
    if user_score.quiz_count > 0:
        accuracy = round(user_score.correct_count / user_score.quiz_count * 100, 1)

    response = f"""
📊 【我的反诈积分】

💰 总积分：{user_score.score} 分
📝 答题次数：{user_score.quiz_count} 次
✅ 正确次数：{user_score.correct_count} 次
🎯 正确率：{accuracy}%
📅 签到天数：{user_score.sign_in_days} 天
""".strip()

    await my_score_cmd.finish(response)


# ==================== 积分排行榜 ====================
leaderboard_cmd = on_command(
    "积分排行",
    aliases={"排行榜", "积分榜", "反诈排行"},
    priority=5,
    block=True
)


@leaderboard_cmd.handle()
async def handle_leaderboard(
    bot: Bot,
    event: Event,
    session: async_scoped_session
):
    """显示积分排行榜"""
    # 私聊不支持排行榜
    if isinstance(event, PrivateMessageEvent):
        await leaderboard_cmd.finish("排行榜仅在群聊中可用，请在群内发送 '积分排行'")

    group_id = _get_group_id(event)

    top_users = await get_leaderboard(session, group_id, limit=10)

    if not top_users:
        await leaderboard_cmd.finish("📊 暂无排行数据，快来答题赚积分吧！")
        return

    # 构建排行榜
    lines = ["🏆 【反诈积分排行榜】", ""]
    medals = ["🥇", "🥈", "🥉"]

    for i, user in enumerate(top_users):
        prefix = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{prefix} {user.user_id[:6]}*** - {user.score} 分")

    await leaderboard_cmd.finish("\n".join(lines))


# ==================== 反诈答题 ====================
quiz_cmd = on_command(
    "反诈答题",
    aliases={"答题", "开始答题"},
    priority=5,
    block=True
)


@quiz_cmd.handle()
async def handle_quiz_start(
    bot: Bot,
    event: Event,
    session: async_scoped_session
):
    """开始答题"""
    user_id = event.get_user_id()
    group_id = _get_group_id(event)

    if group_id:
        from src.database.crud import get_group_config
        config = await get_group_config(session, group_id)
        if not config.quiz_enabled:
            await quiz_cmd.finish("⚠️ 本群已关闭答题功能")

    # 检查是否已有进行中的答题
    if get_quiz_state(user_id):
        await quiz_cmd.finish("⚠️ 您有正在进行的答题，请先完成或等待超时")
        return

    # 获取随机题目
    questions = await get_random_questions(session, count=3)

    if not questions:
        await quiz_cmd.finish("⚠️ 题库暂无题目，请联系管理员添加")
        return

    # 初始化答题会话
    question_msg = await start_quiz_session(user_id, group_id, questions)

    await quiz_cmd.finish(question_msg)


# ==================== 辅助函数 ====================
def _get_group_id(event: Event) -> str | None:
    """获取群号"""
    if isinstance(event, GroupMessageEvent):
        return str(event.group_id)
    return None
