from nonebot import on_command, logger, require, get_bot, get_driver
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session
from src.database.crud import get_group_config, update_group_config

from pathlib import Path
import random


ADMIN = GROUP_ADMIN | GROUP_OWNER | SUPERUSER


push_global = on_command("全局诈骗案例推送", permission=SUPERUSER, priority=9, block=True)

push = on_command("诈骗案例推送", priority=9, block=True)


# 从 nonebot 获取配置
driver = get_driver()
config = driver.config

# 默认全局开关
push_group_default = True
push_private_default = True
hour = getattr(config, "anti_fraud_example_push_hour", 12)
minutu = getattr(config, "anti_fraud_example_push_minute", 0)


async def push_example(id, bot: Bot, type: str):
    """
    type: 'group' or 'private'
    """
    example_dir = Path() / "source" / "example"
    if not example_dir.exists():
        logger.error(f"案例目录 {example_dir} 不存在！")
        return None
    # 获取目录中的所有txt文件
    txts = [file for file in example_dir.iterdir() if file.suffix.lower() == ".txt"]
    if not txts:
        logger.error(f"案例目录 {example_dir} 中没有找到可用案例文件。")
        return None
    # 随机选择一个文件
    txt = random.choice(txts)

    try:
        with open(txt, "r", encoding="utf-8") as f:
            msg = f.read()

        if type == "group":
            await bot.send_group_msg(group_id=id, message=msg)
        elif type == "private":
            await bot.send_private_msg(user_id=id, message=msg)
    except Exception as e:
        logger.warning(f"推送案例失败 ({type}:{id}): {e}")


async def handle_example_push():
    bot: Bot = get_bot()

    from nonebot_plugin_orm import get_session
    from src.database.models import GroupConfig
    from sqlalchemy import select

    # 群聊处理
    try:
        group_list = await bot.get_group_list()

        async with get_session() as session:
            stmt = select(GroupConfig)
            result = await session.execute(stmt)
            all_configs = result.scalars().all()

            # 转为字典以便快速查找: group_id -> config
            config_map = {str(c.group_id): c for c in all_configs}

            for group in group_list:
                gid = str(group["group_id"])
                should_push = push_group_default

                if gid in config_map:
                    should_push = config_map[gid].example_push

                if should_push:
                    await push_example(gid, bot, "group")

    except Exception as e:
        logger.error(f"群聊推送任务出错: {e}")

    # 私聊处理 - 检查每个用户的配置
    from src.database.models import UserConfig

    try:
        friend_list = await bot.get_friend_list()

        async with get_session() as session:
            # 获取所有用户配置
            stmt = select(UserConfig)
            result = await session.execute(stmt)
            all_configs = result.scalars().all()

            # 转为字典: user_id -> config
            user_config_map = {str(c.user_id): c for c in all_configs}

            for friend in friend_list:
                uid = str(friend["user_id"])
                # 默认开启，如果用户配置了则按配置来
                should_push = push_private_default

                if uid in user_config_map:
                    should_push = user_config_map[uid].example_push

                if should_push:
                    await push_example(uid, bot, "private")
    except Exception as e:
        logger.error(f"私聊推送任务出错: {e}")


@scheduler.scheduled_job(
    "cron",
    hour=hour,
    minute=minutu,
)
async def _():
    await handle_example_push()


@push_global.handle()
async def _():
    await handle_example_push()
    await push_global.finish("全局诈骗案例推送成功")


@push.handle()
async def _(bot: Bot, event: Event):
    id = event.get_session_id()
    type = "private"
    if isinstance(event, GroupMessageEvent):
        id = str(event.group_id)
        type = "group"
    await push_example(id, bot, type)
