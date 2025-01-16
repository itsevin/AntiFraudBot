from nonebot import on_command, on_message, logger, get_plugin_config
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import EventPlainText
from nonebot.matcher import Matcher
from utils.config import Config
from utils.init import init_data

from pathlib import Path
import ujson as json


ADMIN = GROUP_ADMIN | GROUP_OWNER | SUPERUSER


all_message = on_message(
    block=False,
    priority=13
)

detection_open = on_command(
    "关键词检测开启",
    priority=8,
    block=True
)

detection_close = on_command(
    "关键词检测关闭",
    priority=8,
    block=True
)


config = get_plugin_config(Config)

detection_group = config.keyword_detection_group
detection_private = config.keyword_detection_private


@all_message.handle()
async def _(event: Event, matcher: Matcher, msg: str = EventPlainText()):
    # 文本消息为空时结束处理
    if not msg:
        return
    
    # 未开启关键词检测时结束处理
    id = event.get_session_id()
    is_private = True
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        is_private = False
    
    try:
        with open("data/data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        await init_data()
        logger.warning("未找到 data/data.json 文件，已进行初始化生成")
        with open("data/data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

    if is_private:
        # 私聊处理
        for single_friend in data['keyword_detection']['friend_list']:
            if str(single_friend['id']) == str(id):
                if not single_friend['keyword_detection']:
                    return
    else:
        # 群聊处理
        for single_group in data['keyword_detection']['group_list']:
            if str(single_group['id']) == str(id):
                if not single_group['keyword_detection']:
                    return

    # 读取关键词列表
    keyword_file = Path("source/keyword.txt")
    if not keyword_file.exists():
        logger.error("关键词文件 source/keyword.txt 不存在！")
        return
    try:
        with open(keyword_file, "r", encoding="utf-8") as f:
            keywords = {line.strip() for line in f if line.strip()}
    except Exception as e:
        logger.error(f"无法读取关键词文件: {e}")
        return

    # 检查消息是否包含关键词
    for keyword in keywords:
        if keyword in msg:
            await all_message.finish(f"检测到敏感词 {keyword} ，请谨防诈骗！！！")
            matcher.stop_propagation()
            break


@detection_open.handle()
async def _(bot: Bot, event: Event):
    id = event.get_session_id()
    is_private = True
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        is_private = False

    # 群聊情况下需要验证是否为管理员
    if not is_private and not await ADMIN(bot, event):
        await detection_open.finish("只有群主或管理员可以开启关键词检测")
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
        for single_friend in data['keyword_detection']['friend_list']:
            if str(single_friend['id']) == str(id):
                flag = True
                single_friend['keyword_detection'] = True  # 修改状态
        if not flag:
            data['keyword_detection']['friend_list'].append(
                {
                    "id": id,
                    "keyword_detection": True
                }
            )
    else:
        # 群聊处理
        flag = False
        for single_group in data['keyword_detection']['group_list']:
            if str(single_group['id']) == str(id):
                flag = True
                single_group['keyword_detection'] = True  # 修改状态
        if not flag:
            data['keyword_detection']['group_list'].append(
                {
                    "id": id,
                    "keyword_detection": True
                }
            )

    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await detection_open.finish("当前会话关键词检测已开启")


@detection_close.handle()
async def _(bot: Bot, event: Event):
    id = event.get_session_id()
    is_private = True
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        is_private = False

    # 群聊情况下需要验证是否为管理员
    if not is_private and not await ADMIN(bot, event):
        await detection_close.finish("只有群主或管理员可以关闭关键词检测")
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
        for single_friend in data['keyword_detection']['friend_list']:
            if str(single_friend['id']) == str(id):
                flag = True
                single_friend['keyword_detection'] = False  # 修改状态
        if not flag:
            data['keyword_detection']['friend_list'].append(
                {
                    "id": id,
                    "keyword_detection": False
                }
            )
    else:
        # 群聊处理
        flag = False
        for single_group in data['keyword_detection']['group_list']:
            if str(single_group['id']) == str(id):
                flag = True
                single_group['keyword_detection'] = False  # 修改状态
        if not flag:
            data['keyword_detection']['group_list'].append(
                {
                    "id": id,
                    "keyword_detection": False
                }
            )

    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await detection_close.finish("当前会话关键词检测已关闭")
