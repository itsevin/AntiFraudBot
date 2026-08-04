from nonebot import on_command, on_message, logger, require
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, Message
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import EventPlainText, CommandArg
from nonebot.matcher import Matcher

require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session

from src.database.crud import (
    get_all_keywords,
    add_keyword,
    remove_keyword,
    log_detection,
    get_group_config,
)

ADMIN = GROUP_ADMIN | GROUP_OWNER | SUPERUSER

# ==================== 事件响应器 ====================

# 消息监听（优先级设置较低，避免阻断其他命令）
all_message = on_message(priority=15, block=False)

# 管理指令
keyword_add = on_command("添加敏感词", permission=ADMIN, priority=5, block=True)
keyword_remove = on_command("删除敏感词", permission=ADMIN, priority=5, block=True)
keyword_list = on_command("敏感词列表", permission=ADMIN, priority=5, block=True)


@all_message.handle()
async def _(
    bot: Bot,
    event: Event,
    session: async_scoped_session,
    matcher: Matcher,
    msg: str = EventPlainText(),
):
    """处理消息监听与关键词检测"""
    if not msg.strip():
        return

    # 0. 如果是发给机器人的消息（私聊或被@），则跳过检测
    # 避免用户咨询诈骗问题时触发误报
    if event.is_tome():
        return

    # 1. 检查功能开关
    # 默认为开启，但在群聊中需检查群配置
    is_enabled = True
    group_id = None

    if isinstance(event, GroupMessageEvent):
        group_id = str(event.group_id)
        config = await get_group_config(session, group_id)
        if not config.keyword_detection:
            is_enabled = False

    # 暂不处理私聊的开关逻辑，默认开启或可扩展为用户表配置
    # 如果已关闭，则直接返回
    if not is_enabled:
        return

    # 2. 获取所有敏感词
    keywords = await get_all_keywords(session)
    if not keywords:
        logger.debug("关键词检测: 敏感词库为空")
        return

    # 3. 匹配检测
    matched_keyword = None
    for kw in keywords:
        if kw.word in msg:
            matched_keyword = kw
            break

    if matched_keyword:
        # 提取字段值，避免 commit 后对象过期导致 LazyLoad 失败
        matched_word = matched_keyword.word
        matched_risk = matched_keyword.risk_level

        # 记录日志 (风险等级用于计算防护指数)
        await log_detection(
            session=session,
            user_id=event.get_user_id(),
            keyword=matched_word,
            message_content=msg,
            group_id=group_id,
            risk_level=matched_risk,
        )

        # 发送警告
        warning_msg = f"⚠️ 警告：检测到敏感词【{matched_word}】\n请注意甄别信息真伪，谨防诈骗！"
        await all_message.finish(warning_msg)
        matcher.stop_propagation()


@keyword_add.handle()
async def _(session: async_scoped_session, args: Message = CommandArg()):
    """添加敏感词"""
    word = args.extract_plain_text().strip()
    if not word:
        await keyword_add.finish("📝 用法：添加敏感词 [词语]")

    success, message = await add_keyword(session, word)
    if success:
        await keyword_add.finish(f"✅ {message}")
    else:
        await keyword_add.finish(f"⚠️ {message}")


@keyword_remove.handle()
async def _(session: async_scoped_session, args: Message = CommandArg()):
    """删除敏感词"""
    word = args.extract_plain_text().strip()
    if not word:
        await keyword_remove.finish("📝 用法：删除敏感词 [词语]")

    success, message = await remove_keyword(session, word)
    if success:
        await keyword_remove.finish(f"✅ {message}")
    else:
        await keyword_remove.finish(f"⚠️ {message}")


@keyword_list.handle()
async def _(session: async_scoped_session):
    """查看敏感词列表"""
    keywords = await get_all_keywords(session)
    if not keywords:
        await keyword_list.finish("📭 当前暂无敏感词")

    # 限制显示数量，防止刷屏
    display_list = [kw.word for kw in keywords]
    count = len(display_list)

    msg = f"📋 敏感词列表 ({count}个):\n\n" + "、".join(display_list)
    await keyword_list.finish(msg)
