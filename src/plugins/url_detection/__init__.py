from nonebot import on_command, on_message, logger, get_plugin_config
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import EventPlainText
from nonebot.matcher import Matcher
from utils.config import Config
from utils.init import init_data
from .api import url_detection_api

import ujson as json
import re


ADMIN = GROUP_ADMIN | GROUP_OWNER | SUPERUSER


all_message = on_message(
    block=False,
    priority=12
)

detection_open = on_command(
    "链接检测开启",
    priority=8,
    block=True
)

detection_close = on_command(
    "链接检测关闭",
    priority=8,
    block=True
)


config = get_plugin_config(Config)

detection_group = config.url_detection_group
detection_private = config.url_detection_private


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
        for single_friend in data['url_detection']['friend_list']:
            if str(single_friend['id']) == str(id):
                if not single_friend['url_detection']:
                    return
    else:
        # 群聊处理
        for single_group in data['url_detection']['group_list']:
            if str(single_group['id']) == str(id):
                if not single_group['url_detection']:
                    return

    # 使用正则表达式查找所有匹配的 URL
    url_pattern = r'(https?://[^\s<>"]+|www\.[^\s<>"]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s<>"]*)'
    urls = re.findall(url_pattern, msg)
    urls = list(set(urls)) # 去重
    for url in urls:
        result = await url_detection_api(url)
        if not result:
            return
        labels = result

        # 未被风险标记的或正常网站
        if labels == 'unmarked_url' or labels == 'safe_url' or labels == 'nonLabel':
            continue
        elif labels == 'sexual_url':
            msg = f'检测到危险网站 {url} ，请勿打开，谨防诈骗！！！'
        elif labels == 'gambling_url':
            msg = f'检测到疑似赌博网站 {url} ，请勿打开，请谨防诈骗！！！'
        elif labels == 'phishing_url':
            msg = f'检测到疑似钓鱼网站 {url} ，请勿打开，请谨防诈骗！！！'
        elif labels == 'other_risk_url':
            msg = f'检测到疑似欺诈和含有其他风险的网站 {url} ，请勿打开，请谨防诈骗！！！'
        else:
            logger.warning(f"链接检测接口返回未知链接标签：f{labels}")
            continue
        await all_message.send(msg)


@detection_open.handle()
async def _(bot: Bot, event: Event):
    id = event.get_session_id()
    is_private = True
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        is_private = False

    # 群聊情况下需要验证是否为管理员
    if not is_private and not await ADMIN(bot, event):
        await detection_open.finish("只有群主或管理员可以开启链接检测")
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
        for single_friend in data['url_detection']['friend_list']:
            if str(single_friend['id']) == str(id):
                flag = True
                single_friend['url_detection'] = True  # 修改状态
        if not flag:
            data['url_detection']['friend_list'].append(
                {
                    "id": id,
                    "url_detection": True
                }
            )
    else:
        # 群聊处理
        flag = False
        for single_group in data['url_detection']['group_list']:
            if str(single_group['id']) == str(id):
                flag = True
                single_group['url_detection'] = True  # 修改状态
        if not flag:
            data['url_detection']['group_list'].append(
                {
                    "id": id,
                    "url_detection": True
                }
            )

    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await detection_open.finish("当前会话链接检测已开启")


@detection_close.handle()
async def _(bot: Bot, event: Event):
    id = event.get_session_id()
    is_private = True
    if '_' in id:  # 群聊情况下拆分出群聊 id
        id = id.split("_")[1]
        is_private = False

    # 群聊情况下需要验证是否为管理员
    if not is_private and not await ADMIN(bot, event):
        await detection_close.finish("只有群主或管理员可以关闭链接检测")
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
        for single_friend in data['url_detection']['friend_list']:
            if str(single_friend['id']) == str(id):
                flag = True
                single_friend['url_detection'] = False  # 修改状态
        if not flag:
            data['url_detection']['friend_list'].append(
                {
                    "id": id,
                    "url_detection": False
                }
            )
    else:
        # 群聊处理
        flag = False
        for single_group in data['url_detection']['group_list']:
            if str(single_group['id']) == str(id):
                flag = True
                single_group['url_detection'] = False  # 修改状态
        if not flag:
            data['url_detection']['group_list'].append(
                {
                    "id": id,
                    "url_detection": False
                }
            )

    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await detection_close.finish("当前会话链接检测已关闭")
