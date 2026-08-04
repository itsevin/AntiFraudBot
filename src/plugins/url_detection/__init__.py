from nonebot import on_command, on_message, logger, require
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import EventPlainText
from nonebot.matcher import Matcher
from .api import url_detection_api

require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session
from src.database.crud import get_group_config, update_group_config, log_detection

import re

ADMIN = GROUP_ADMIN | GROUP_OWNER | SUPERUSER


all_message = on_message(block=False, priority=12)

detection_open = on_command("链接检测开启", priority=8, block=True)

detection_close = on_command("链接检测关闭", priority=8, block=True)


@all_message.handle()
async def _(
    event: Event, matcher: Matcher, session: async_scoped_session, msg: str = EventPlainText()
):
    # 文本消息为空时结束处理
    if not msg:
        return

    # 未开启检测时结束处理
    is_enabled = True
    if isinstance(event, GroupMessageEvent):
        group_id = str(event.group_id)
        config = await get_group_config(session, group_id)
        if not config.url_detection:
            is_enabled = False

    if not is_enabled:
        return

    # 使用正则表达式查找所有匹配的 URL
    url_pattern = r'(https?://[^\s<>"]+|www\.[^\s<>"]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s<>"]*)'
    urls = re.findall(url_pattern, msg)
    urls = list(set(urls))  # 去重
    for url in urls:
        # 跳过看起来像IP但其实不是URL的纯数字串（简单过滤）
        if re.match(r"^\d+$", url):
            continue

        result = await url_detection_api(url)
        if not result:
            continue
        labels = result

        # 未被风险标记的或正常网站
        if labels == "unmarked_url" or labels == "safe_url" or labels == "nonLabel":
            continue

        msg_template = "⚠️ 检测到{desc} {url} ，请勿打开，谨防诈骗！！！"
        warning_msg = ""

        if labels == "sexual_url":
            warning_msg = msg_template.format(desc="危险网站", url=url)
            risk_level = 3
        elif labels == "gambling_url":
            warning_msg = msg_template.format(desc="疑似赌博网站", url=url)
            risk_level = 4
        elif labels == "phishing_url":
            warning_msg = msg_template.format(desc="疑似钓鱼网站", url=url)
            risk_level = 5
        elif labels == "other_risk_url":
            warning_msg = msg_template.format(desc="疑似欺诈/风险网站", url=url)
            risk_level = 4
        else:
            logger.warning(f"链接检测接口返回未知标签：{labels}")
            continue

        # 记录到数据库 (接入大屏可视化)
        group_id = str(event.group_id) if isinstance(event, GroupMessageEvent) else None
        await log_detection(
            session=session,
            user_id=event.get_user_id(),
            keyword=f"[URL] {labels}",
            message_content=f"检测到恶意链接: {url}",
            group_id=group_id,
            risk_level=risk_level,
        )

        await all_message.send(warning_msg)


@detection_open.handle()
async def _(bot: Bot, event: Event, session: async_scoped_session):
    # 群聊情况下需要验证是否为管理员
    if isinstance(event, GroupMessageEvent) and not await ADMIN(bot, event):
        await detection_open.finish("只有群主或管理员可以开启链接检测")
        return

    if isinstance(event, GroupMessageEvent):
        group_id = str(event.group_id)
        await update_group_config(session, group_id, url_detection=True)
        await detection_open.finish("✅ 当前群聊链检测已开启")
    else:
        # 私聊暂不支持配置持久化，或者需要扩展UserConfig
        await detection_open.finish("⚠️ 目前仅支持在群聊中配置此功能")


@detection_close.handle()
async def _(bot: Bot, event: Event, session: async_scoped_session):
    # 群聊情况下需要验证是否为管理员
    if isinstance(event, GroupMessageEvent) and not await ADMIN(bot, event):
        await detection_close.finish("只有群主或管理员可以关闭链接检测")
        return

    if isinstance(event, GroupMessageEvent):
        group_id = str(event.group_id)
        await update_group_config(session, group_id, url_detection=False)
        await detection_close.finish("⛔ 当前群聊链接检测已关闭")
    else:
        await detection_close.finish("⚠️ 目前仅支持在群聊中配置此功能")
