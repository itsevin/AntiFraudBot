from nonebot import on_command, on_message, logger, get_plugin_config
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event
from nonebot.adapters.onebot.v11.permission import GROUP_ADMIN, GROUP_OWNER
from nonebot.params import EventPlainText, CommandArg
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

keyword_add = on_command(
    "添加敏感词",
    permission=ADMIN,
    priority=8,
    block=True
)

keyword_remove = on_command(
    "删除敏感词",
    permission=ADMIN,
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


@keyword_add.handle()
async def _(bot: Bot, event: Event, args=CommandArg()):
    keyword = args.extract_plain_text().strip()
    if not keyword:
        await keyword_add.finish("请输入要添加的敏感词，格式：添加敏感词 [词语]")
        return
    
    keyword_file = Path("source/keyword.txt")
    
    # 读取现有关键词
    existing_keywords = set()
    if keyword_file.exists():
        try:
            with open(keyword_file, "r", encoding="utf-8") as f:
                existing_keywords = {line.strip() for line in f if line.strip()}
        except Exception as e:
            logger.error(f"无法读取关键词文件: {e}")
            await keyword_add.finish("读取关键词文件失败")
            return
    
    # 检查是否已存在
    if keyword in existing_keywords:
        await keyword_add.finish(f"敏感词 '{keyword}' 已存在")
        return
    
    # 添加新关键词
    existing_keywords.add(keyword)
    
    try:
        # 读取原文件保持顺序
        original_keywords = []
        if keyword_file.exists():
            with open(keyword_file, "r", encoding="utf-8") as f:
                original_keywords = [line.strip() for line in f if line.strip()]
        
        # 如果是新关键词，添加到末尾
        if keyword not in original_keywords:
            original_keywords.append(keyword)
        
        with open(keyword_file, "w", encoding="utf-8") as f:
            for kw in original_keywords:
                f.write(kw + "\n")
    except Exception as e:
        logger.error(f"无法写入关键词文件: {e}")
        await keyword_add.finish("添加敏感词失败")
        return
    
    await keyword_add.finish(f"成功添加敏感词：{keyword}")


@keyword_remove.handle()
async def _(bot: Bot, event: Event, args=CommandArg()):
    keyword = args.extract_plain_text().strip()
    if not keyword:
        await keyword_remove.finish("请输入要删除的敏感词，格式：删除敏感词 [词语]")
        return
    
    keyword_file = Path("source/keyword.txt")
    
    if not keyword_file.exists():
        await keyword_remove.finish("关键词文件不存在")
        return
    
    # 读取现有关键词，保持顺序
    try:
        with open(keyword_file, "r", encoding="utf-8") as f:
            original_keywords = [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"无法读取关键词文件: {e}")
        await keyword_remove.finish("读取关键词文件失败")
        return
    
    # 检查是否存在
    if keyword not in original_keywords:
        await keyword_remove.finish(f"敏感词 '{keyword}' 不存在")
        return
    
    # 删除关键词，保持其他关键词的原有顺序
    original_keywords.remove(keyword)
    
    try:
        with open(keyword_file, "w", encoding="utf-8") as f:
            for kw in original_keywords:
                f.write(kw + "\n")
    except Exception as e:
        logger.error(f"无法写入关键词文件: {e}")
        await keyword_remove.finish("删除敏感词失败")
        return
    
    await keyword_remove.finish(f"成功删除敏感词：{keyword}")
