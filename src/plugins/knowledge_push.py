from nonebot import on_command, logger, require, get_plugin_config, get_bot
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment
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
    "全局反诈知识点推送",
    permission=SUPERUSER,
    priority=9,
    block=True
)

push = on_command(
    "反诈知识点推送",
    priority=9,
    block=True
)

push_open = on_command(
    "反诈知识点推送开启",
    priority=8,
    block=True
)

push_close = on_command(
    "反诈知识点推送关闭",
    priority=8,
    block=True
)


config = get_plugin_config(Config)

push_group = config.anti_fraud_knowledge_push_group
push_private = config.anti_fraud_knowledge_push_private
hour = config.anti_fraud_knowledge_push_hour
minutu = config.anti_fraud_knowledge_push_minute


async def push_knowledge(id, bot: Bot, type: str):
    '''
    type: 'group' or 'private'
    '''
    knowledge_dir = Path() / "source" / "knowledge"
    if not knowledge_dir.exists():
        logger.error(f"知识点图片目录 {knowledge_dir} 不存在！")
        return None
    # 获取目录中的所有图片文件
    images = [file for file in knowledge_dir.iterdir() if file.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.webp'}]
    if not images:
        logger.error(f"知识点图片目录 {knowledge_dir} 中没有找到可用知识点图片文件。")
        return None
    # 随机选择一张图片文件
    image = random.choice(images)

    msg = MessageSegment.image(image)
    if type == 'group':
        await bot.send_group_msg(group_id=id, message=msg)
    elif type == 'private':
        await bot.send_private_msg(user_id=id, message=msg)


async def handle_knowledge_push():
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
        for single_group in data['knowledge_push']['group_list']:
            if str(single_group['id']) == str(id):
                flag = True
                if single_group['knowledge_push']:
                    await push_knowledge(id, bot, 'group')
        if not flag and push_group:
            await push_knowledge(id, bot, 'group')
    
    # 私聊处理
    friend_list = await bot.call_api("get_friend_list")
    for friend in friend_list:
        id = friend['user_id']
        flag = False
        for single_friend in data['knowledge_push']['friend_list']:
            if str(single_friend['id']) == str(id):
                flag = True
                if single_friend['knowledge_push']:
                    await push_knowledge(id, bot, 'private')
        if not flag and push_private:
            await push_knowledge(id, bot, 'private')


@scheduler.scheduled_job(
    "cron",
    hour=hour,
    minute=minutu,
)
async def _():
    await handle_knowledge_push()


@push_global.handle()
async def _():
    await handle_knowledge_push()
    await push_global.finish("全局反诈知识点推送成功")


@push.handle()
async def _(bot: Bot, event: Event):
    id = event.get_session_id()
    type = 'private'
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        type = 'group'
    await push_knowledge(id, bot, type)


@push_open.handle()
async def _(bot: Bot, event: Event):
    id = event.get_session_id()
    is_private = True
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        is_private = False

    # 群聊情况下需要验证是否为管理员
    if not is_private and not await ADMIN(bot, event):
        await push_open.finish("只有群主或管理员可以开启反诈知识点推送")
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
        for single_friend in data['knowledge_push']['friend_list']:
            if str(single_friend['id']) == str(id):
                flag = True
                single_friend['knowledge_push'] = True  # 修改状态
        if not flag:
            data['knowledge_push']['friend_list'].append(
                {
                    "id": id,
                    "knowledge_push": True
                }
            )
    else:
        # 群聊处理
        flag = False
        for single_group in data['knowledge_push']['group_list']:
            if str(single_group['id']) == str(id):
                flag = True
                single_group['knowledge_push'] = True  # 修改状态
        if not flag:
            data['knowledge_push']['group_list'].append(
                {
                    "id": id,
                    "knowledge_push": True
                }
            )

    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await push_open.finish("当前会话反诈知识点推送已开启")


@push_close.handle()
async def _(bot: Bot, event: Event):
    id = event.get_session_id()
    is_private = True
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        is_private = False

    # 群聊情况下需要验证是否为管理员
    if not is_private and not await ADMIN(bot, event):
        await push_close.finish("只有群主或管理员可以关闭反诈知识点推送")
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
        for single_friend in data['knowledge_push']['friend_list']:
            if str(single_friend['id']) == str(id):
                flag = True
                single_friend['knowledge_push'] = False  # 修改状态
        if not flag:
            data['knowledge_push']['friend_list'].append(
                {
                    "id": id,
                    "knowledge_push": False
                }
            )
    else:
        # 群聊处理
        flag = False
        for single_group in data['knowledge_push']['group_list']:
            if str(single_group['id']) == str(id):
                flag = True
                single_group['knowledge_push'] = False  # 修改状态
        if not flag:
            data['knowledge_push']['group_list'].append(
                {
                    "id": id,
                    "knowledge_push": False
                }
            )

    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await push_close.finish("当前会话反诈知识点推送已关闭")
