from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent, PrivateMessageEvent

help_cmd = on_command('help', aliases={'帮助', '菜单', '功能'}, priority=1, block=True)

# 群聊菜单
group_menu = """🛡️ 反诈小助手功能清单
————————————
[🔍智能鉴诈]
发送 "鉴诈+文本" (如: 鉴诈 我是秦始皇)

[🤖智能对话]
@机器人 [问题] (支持多轮对话)
清除对话 - 重置对话历史

[🧠反诈答题]
指令: 反诈答题 | 签到 | 我的积分 | 积分排行

[🛡️安全防护]
支持: 关键词检测 | 链接检测 (自动运行)

[📢推送服务]
指令: 反诈知识点推送 | 诈骗案例推送

[⚙️管理设置] (仅管理员)
指令: 查看配置 | 开启/关闭 [功能]
指令: 添加/删除敏感词 [词语]
功能: 关键词检测 | 链接检测 | 知识推送 | 案例推送

Tip: 每天12点自动推送反诈知识
项目: https://github.com/itsevin/AntiFraudBot"""

# 私聊菜单
private_menu = """👋 欢迎咨询反诈小助手！
这里是您的私人反诈顾问。

[🤖 智能对话]
直接发送消息即可跟我聊天
• "如何识别杀猪盘？"
• "这条短信是诈骗吗？"

[🔍 主动鉴诈]
发送 "鉴诈+文本"
• 帮您分析可疑话术/短信

[📚 反诈知识]
发送 "反诈知识点推送" 或 "诈骗案例推送"

[⚙️ 推送设置]
发送 "开启/关闭 知识推送" 或 "查看配置"

💡 签到、积分、排行榜等互动功能请在群聊中使用"""


@help_cmd.handle()
async def _(bot: Bot, event: MessageEvent):
    if isinstance(event, PrivateMessageEvent):
        await help_cmd.finish(private_menu)
    else:
        await help_cmd.finish(group_menu)
