from nonebot import on_command, on_message
from nonebot.rule import to_me

help = on_command(
    'help',
    aliases={'帮助', '功能', '菜单', 'menu'},
    block=True,
    priority=10
)

at = on_message(
    rule=to_me(),
    block=True,
    priority=15
)

fzzsd = on_command(
    '反诈知识点',
    block=True,
    priority=10
)

zpal = on_command(
    '诈骗案例',
    block=True,
    priority=10
)

gjcsb = on_command(
    '关键词检测',
    block=True,
    priority=10
)

ljjc = on_command(
    '链接检测',
    block=True,
    priority=10
)

about = on_command(
    'About',
    aliases={'about', 'ABOUT'},
    block=True,
    priority=10
)


help_data = '''您好！我是反诈小助手，随时为您提供帮助。以下是我的功能菜单：

1️⃣ 反诈知识点 - 学习常见的反诈知识，提升防骗意识
2️⃣ 诈骗案例 -  查看真实诈骗案例，了解诈骗手法
3️⃣ 关键词检测 - 帮助您识别聊天中的潜在诈骗信息
4️⃣ 链接检测 - 检查可疑链接是否安全
5️⃣ About - 了解关于反诈小助手的更多信息

发送关键词（如“反诈知识点”）即可了解更多内容！'''


@help.handle()
async def _():
    await help.finish(help_data)

@at.handle()
async def _():
    await at.finish(help_data)

@fzzsd.handle()
async def _():
    msg = '''指令列表：

🚨 反诈知识点推送：立即推送本次会话的反诈知识点
⏰ 反诈知识点推送开启：启动当前会话每日定时反诈知识点推送功能，群聊仅限管理使用
⛔ 反诈知识点推送关闭：关闭当前会话每日定时反诈知识点推送功能，群聊仅限管理使用
🌐 全局反诈知识点推送：仅限超级管理员，用于全局推送防诈骗知识

通过这些指令，及时获取防诈骗知识，保障您的财产安全！'''
    await fzzsd.finish(msg)

@zpal.handle()
async def _():
    msg = '''指令列表：

🚨 诈骗案例推送：立即推送本次会话的诈骗案例
⏰ 诈骗案例推送开启：启动当前会话每日定时诈骗案例推送功能，群聊仅限管理使用
⛔ 诈骗案例推送关闭：关闭当前会话每日定时诈骗案例推送功能，群聊仅限管理使用
🌐 全局诈骗案例推送：仅限超级管理员，用于全局推送诈骗案例

通过这些指令，了解最新诈骗案例，助您提高警惕，守护财产安全！'''
    await zpal.finish(msg)

@gjcsb.handle()
async def _():
    msg = '''指令列表：

🚨 关键词自动检测，遇到敏感关键词会报警提示
🔒 关键词检测开启：启动当前会话关键词检测，群聊仅限管理使用
🔓 关键词检测关闭：关闭当前会话关键词检测，群聊仅限管理使用'''
    await gjcsb.finish(msg)

@ljjc.handle()
async def _():
    msg = '''指令列表：

🚨 链接自动检测，遇到危险链接会报警提示
🔒 链接检测开启：启动当前会话链接检测，群聊仅限管理使用
🔓 链接检测关闭：关闭当前会话链接检测，群聊仅限管理使用'''
    await ljjc.finish(msg)

@about.handle()
async def _():
    msg = '''🌟反诈小助手🌟
📜开源地址：
https://github.com/itsevin/AntiFraudBot'''
    await about.finish(msg)