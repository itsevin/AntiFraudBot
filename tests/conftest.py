import sys
from pathlib import Path

import nonebot


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

nonebot.init(
    driver="~fastapi",
    web_admin_password="test-only-password-123",
    jwt_secret="test-only-jwt-secret-1234567890",
    web_cors_origins=["http://127.0.0.1:8000"],
)
nonebot.load_plugin("nonebot_plugin_orm")
