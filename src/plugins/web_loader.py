from nonebot import get_driver, logger
import uvicorn
import threading
from src.web.app import app as web_app

driver = get_driver()
config = driver.config
# 获取 Web 监听地址和端口。默认仅监听本机，公网部署应由反向代理接入。
web_host = getattr(config, 'web_host', '127.0.0.1')
web_port = getattr(config, 'web_port', 8000)

def run_web_server():
    """在独立线程中运行 Web 服务"""
    port = web_port
    logger.info(f"正在启动 Web 管理后台 (Port: {port})...")
    # log_config=None 禁止 uvicorn 接管日志，避免重复/冲突
    try:
        uvicorn.run(web_app, host=web_host, port=port, log_config=None)
    except Exception as e:
        logger.error(f"Web 管理后台启动失败: {e}")

@driver.on_startup
async def _():
    # 使用守护线程启动 Web 服务，这样主进程退出时它也会退出
    t = threading.Thread(target=run_web_server, daemon=True)
    t.start()
    logger.info("Web 管理后台线程已启动")
