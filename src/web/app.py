# -*- coding: utf-8 -*-
"""
Web 管理后台 - FastAPI 服务器
提供数据统计 API 和管理界面
"""

from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path

from nonebot import get_driver, require

require("nonebot_plugin_orm")

from .api import stats, keywords, quiz, auth, visuals
from fastapi.middleware.cors import CORSMiddleware
from .security import parse_cors_origins

# 创建 FastAPI 应用
app = FastAPI(
    title="反诈防御系统管理后台",
    description="AntiFraudBot Web Dashboard",
    version="2.0.0"
)

driver = get_driver()
cors_origins = parse_cors_origins(getattr(driver.config, "web_cors_origins", None))

# 配置 CORS：仅允许显式可信来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# 注册 API 路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证授权"])
protected = [Depends(auth.get_current_active_user)]
app.include_router(visuals.router, prefix="/api/visuals", tags=["大屏可视化"], dependencies=protected)
app.include_router(stats.router, prefix="/api/stats", tags=["基础统计"], dependencies=protected)
app.include_router(keywords.router, prefix="/api/keywords", tags=["敏感词管理"], dependencies=protected)
app.include_router(quiz.router, prefix="/api/quiz", tags=["题库管理"], dependencies=protected)

# 静态文件目录
STATIC_DIR = Path(__file__).parent / "frontend_v2" / "dist"

# 挂载静态文件
if STATIC_DIR.exists():
    # 挂载 /static 用于兼容旧版或手动访问
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # 挂载 /assets 用于 Vite 构建的新版前端资源
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
        print(f"✅ 已挂载前端资源: {assets_dir}")
    else:
        print(f"❌ 未找到 assets 目录: {assets_dir}")
else:
    print(f"⚠️ 未找到前端构建目录: {STATIC_DIR}")


@app.get("/", response_class=HTMLResponse)
async def index():
    """入口页"""
    index_html = STATIC_DIR / "index.html"
    if index_html.exists():
        return FileResponse(index_html)
    return HTMLResponse("<h1>反诈防御系统</h1><p>正在升级中...</p>")


@driver.on_startup
async def startup():
    """服务启动时的初始化"""
    from nonebot import logger
    logger.info("Web 管理后台已启动")


# 获取 ASGI 应用用于挂载
def get_asgi_app():
    return app
