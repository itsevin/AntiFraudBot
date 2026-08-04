# -*- coding: utf-8 -*-
"""
配置管理插件
群聊：允许群管理员通过指令控制各项功能的开关
私聊：允许用户控制推送开关
"""

from nonebot import on_command, require
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg
from nonebot.adapters import Message

require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session

from src.database.crud import (
    update_group_config,
    get_group_config,
    get_user_config,
    update_user_config
)

# 权限设置：群主、群管、超管
ADMIN = GROUP_ADMIN | GROUP_OWNER | SUPERUSER

# 群聊功能映射表
GROUP_FEATURE_MAP = {
    "关键词检测": "keyword_detection",
    "URL检测": "url_detection",
    "链接检测": "url_detection",
    "AI分析": "ai_analysis",
    "智能鉴诈": "ai_analysis",
    "答题功能": "quiz_enabled",
    "反诈答题": "quiz_enabled",
    "知识推送": "knowledge_push",
    "反诈知识点推送": "knowledge_push",
    "案例推送": "example_push",
    "诈骗案例推送": "example_push"
}

# 私聊功能映射表（用户可配置的功能）
PRIVATE_FEATURE_MAP = {
    "知识推送": "knowledge_push",
    "反诈知识点推送": "knowledge_push",
    "案例推送": "example_push",
    "诈骗案例推送": "example_push"
}

# 注册指令（不限制权限，在处理函数中判断）
enable_cmd = on_command("开启", priority=5, block=True)
disable_cmd = on_command("关闭", priority=5, block=True)
view_config_cmd = on_command("查看配置", priority=5, block=True)


@enable_cmd.handle()
async def handle_enable(
    bot: Bot,
    event: MessageEvent,
    session: async_scoped_session,
    args: Message = CommandArg()
):
    """开启指定功能"""
    feature_name = args.extract_plain_text().strip()

    if isinstance(event, GroupMessageEvent):
        # 群聊：检查管理员权限
        user_id = str(event.user_id)
        group_id = str(event.group_id)

        # 检查权限
        member_info = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
        role = member_info.get("role", "member")
        superusers = getattr(bot.config, "superusers", set())

        if role not in ["owner", "admin"] and user_id not in superusers:
            await enable_cmd.finish("⚠️ 仅群管理员可使用此命令")

        if not feature_name:
            await enable_cmd.finish("⚠️ 请输入要开启的功能名称，例如：开启 答题功能")

        db_field = GROUP_FEATURE_MAP.get(feature_name)
        if not db_field:
            await enable_cmd.finish(f"⚠️ 未知的功能名称：{feature_name}\n支持的功能：{', '.join(GROUP_FEATURE_MAP.keys())}")

        await update_group_config(session, group_id, **{db_field: True})
        await enable_cmd.finish(f"✅ 已开启本群的【{feature_name}】功能")

    elif isinstance(event, PrivateMessageEvent):
        # 私聊：用户配置
        user_id = event.get_user_id()

        if not feature_name:
            await enable_cmd.finish("⚠️ 请输入要开启的功能名称，例如：开启 知识推送")

        db_field = PRIVATE_FEATURE_MAP.get(feature_name)
        if not db_field:
            await enable_cmd.finish(f"⚠️ 未知的功能名称：{feature_name}\n私聊可配置：{', '.join(PRIVATE_FEATURE_MAP.keys())}")

        await update_user_config(session, user_id, **{db_field: True})
        await enable_cmd.finish(f"✅ 已开启【{feature_name}】")


@disable_cmd.handle()
async def handle_disable(
    bot: Bot,
    event: MessageEvent,
    session: async_scoped_session,
    args: Message = CommandArg()
):
    """关闭指定功能"""
    feature_name = args.extract_plain_text().strip()

    if isinstance(event, GroupMessageEvent):
        # 群聊：检查管理员权限
        user_id = str(event.user_id)
        group_id = str(event.group_id)

        # 检查权限
        member_info = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
        role = member_info.get("role", "member")
        superusers = getattr(bot.config, "superusers", set())

        if role not in ["owner", "admin"] and user_id not in superusers:
            await disable_cmd.finish("⚠️ 仅群管理员可使用此命令")

        if not feature_name:
            await disable_cmd.finish("⚠️ 请输入要关闭的功能名称，例如：关闭 答题功能")

        db_field = GROUP_FEATURE_MAP.get(feature_name)
        if not db_field:
            await disable_cmd.finish(f"⚠️ 未知的功能名称：{feature_name}\n支持的功能：{', '.join(GROUP_FEATURE_MAP.keys())}")

        await update_group_config(session, group_id, **{db_field: False})
        await disable_cmd.finish(f"⛔ 已关闭本群的【{feature_name}】功能")

    elif isinstance(event, PrivateMessageEvent):
        # 私聊：用户配置
        user_id = event.get_user_id()

        if not feature_name:
            await disable_cmd.finish("⚠️ 请输入要关闭的功能名称，例如：关闭 知识推送")

        db_field = PRIVATE_FEATURE_MAP.get(feature_name)
        if not db_field:
            await disable_cmd.finish(f"⚠️ 未知的功能名称：{feature_name}\n私聊可配置：{', '.join(PRIVATE_FEATURE_MAP.keys())}")

        await update_user_config(session, user_id, **{db_field: False})
        await disable_cmd.finish(f"⛔ 已关闭【{feature_name}】")


@view_config_cmd.handle()
async def handle_view_config(
    bot: Bot,
    event: MessageEvent,
    session: async_scoped_session
):
    """查看当前配置"""
    status_emoji = lambda x: "✅" if x else "⛔"

    if isinstance(event, GroupMessageEvent):
        # 群聊：检查管理员权限
        user_id = str(event.user_id)
        group_id = str(event.group_id)

        # 检查权限
        member_info = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
        role = member_info.get("role", "member")
        superusers = getattr(bot.config, "superusers", set())

        if role not in ["owner", "admin"] and user_id not in superusers:
            await view_config_cmd.finish("⚠️ 仅群管理员可使用此命令")

        config = await get_group_config(session, group_id)

        msg = f"""
⚙️ 【当前群配置】

{status_emoji(config.keyword_detection)} 关键词检测
{status_emoji(config.url_detection)} URL链接检测
{status_emoji(config.ai_analysis)} AI智能鉴诈
{status_emoji(config.quiz_enabled)} 反诈答题
{status_emoji(config.knowledge_push)} 知识推送
{status_emoji(config.example_push if config.example_push is not None else True)} 案例推送

💡 发送 '开启/关闭 [功能名]' 可修改配置
        """.strip()

        await view_config_cmd.finish(msg)

    elif isinstance(event, PrivateMessageEvent):
        # 私聊：用户配置
        user_id = event.get_user_id()
        config = await get_user_config(session, user_id)

        msg = f"""
⚙️ 【我的推送设置】

{status_emoji(config.knowledge_push)} 知识推送
{status_emoji(config.example_push)} 案例推送

💡 发送 '开启/关闭 知识推送' 可修改配置
        """.strip()

        await view_config_cmd.finish(msg)
