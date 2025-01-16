from nonebot import on_command, logger, require, get_plugin_config, get_bot
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from utils.config import Config
from utils.init import init_data

require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler

from pathlib import Path
import ujson as json
import random


ADMIN = GROUP_ADMIN | GROUP_OWNER | SUPERUSER


push_global = on_command(
    "全局诈骗案例推送",
    permission=SUPERUSER,
    priority=9,
    block=True
)

push = on_command(
    "诈骗案例推送",
    priority=9,
    block=True
)

push_open = on_command(
    "诈骗案例推送开启",
    priority=8,
    block=True
)

push_close = on_command(
    "诈骗案例推送关闭",
    priority=8,
    block=True
)


config = get_plugin_config(Config)

push_group = config.anti_fraud_example_push_group
push_private = config.anti_fraud_example_push_private
hour = config.anti_fraud_example_push_hour
minutu = config.anti_fraud_example_push_minute


async def push_example(id, bot: Bot, type: str):
    '''
    type: 'group' or 'private'
    '''
    example_dir = Path() / "source" / "example"
    if not example_dir.exists():
        logger.error(f"案例目录 {example_dir} 不存在！")
        return None
    # 获取目录中的所有txt文件
    txts = [file for file in example_dir.iterdir() if file.suffix.lower() == '.txt']
    if not txts:
        logger.error(f"案例目录 {example_dir} 中没有找到可用案例文件。")
        return None
    # 随机选择一个文件
    txt = random.choice(txts)
    with open(txt, "r", encoding="utf-8") as f:
        msg = f.read()

    if type == 'group':
        await bot.send_group_msg(group_id=id, message=msg)
    elif type == 'private':
        await bot.send_private_msg(user_id=id, message=msg)


async def handle_example_push():
    bot: Bot = get_bot()

    try:
        with open("data/data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        await init_data()
        logger.warning("未找到 data/data.json 文件，已进行初始化生成")
        with open("data/data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

    # 群聊处理
    group_list = await bot.call_api("get_group_list")
    for group in group_list:
        id = group['group_id']
        flag = False
        for single_group in data['example_push']['group_list']:
            if str(single_group['id']) == str(id):
                flag = True
                if single_group['example_push']:
                    await push_example(id, bot, 'group')
        if not flag and push_group:
            await push_example(id, bot, 'group')
    
    # 私聊处理
    friend_list = await bot.call_api("get_friend_list")
    for friend in friend_list:
        id = friend['user_id']
        flag = False
        for single_friend in data['example_push']['friend_list']:
            if str(single_friend['id']) == str(id):
                flag = True
                if single_friend['example_push']:
                    await push_example(id, bot, 'private')
        if not flag and push_private:
            await push_example(id, bot, 'private')


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
    type = 'private'
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        type = 'group'
    await push_example(id, bot, type)


@push_open.handle()
async def _(bot: Bot, event: Event):
    id = event.get_session_id()
    is_private = True
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        is_private = False

    # 群聊情况下需要验证是否为管理员
    if not is_private and not await ADMIN(bot, event):
        await push_open.finish("只有群主或管理员可以开启诈骗案例推送")
        return
    
    try:
        with open("data/data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        await init_data()
        logger.warning("未找到 data/data.json 文件，已进行初始化生成")
        with open("data/data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

    if is_private:
        #私聊处理
        flag = False
        for single_friend in data['example_push']['friend_list']:
            if str(single_friend['id']) == str(id):
                flag = True
                single_friend['example_push'] = True  # 修改状态
        if not flag:
            data['example_push']['friend_list'].append(
                {
                    "id": id,
                    "example_push": True
                }
            )
    else:
        # 群聊处理
        flag = False
        for single_group in data['example_push']['group_list']:
            if str(single_group['id']) == str(id):
                flag = True
                single_group['example_push'] = True  # 修改状态
        if not flag:
            data['example_push']['group_list'].append(
                {
                    "id": id,
                    "example_push": True
                }
            )

    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await push_open.finish("当前会话诈骗案例推送已开启")


@push_close.handle()
async def _(bot: Bot, event: Event):
    id = event.get_session_id()
    is_private = True
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        is_private = False

    # 群聊情况下需要验证是否为管理员
    if not is_private and not await ADMIN(bot, event):
        await push_close.finish("只有群主或管理员可以关闭诈骗案例推送")
        return

    try:
        with open("data/data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        await init_data()
        logger.warning("未找到 data/data.json 文件，已进行初始化生成")
        with open("data/data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

    if is_private:
        #私聊处理
        flag = False
        for single_friend in data['example_push']['friend_list']:
            if str(single_friend['id']) == str(id):
                flag = True
                single_friend['example_push'] = False  # 修改状态
        if not flag:
            data['example_push']['friend_list'].append(
                {
                    "id": id,
                    "example_push": False
                }
            )
    else:
        # 群聊处理
        flag = False
        for single_group in data['example_push']['group_list']:
            if str(single_group['id']) == str(id):
                flag = True
                single_group['example_push'] = False  # 修改状态
        if not flag:
            data['example_push']['group_list'].append(
                {
                    "id": id,
                    "example_push": False
                }
            )

    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await push_close.finish("当前会话诈骗案例推送已关闭")
