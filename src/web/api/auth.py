from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from nonebot import get_driver
import secrets
import os
from pathlib import Path

from src.web.security import (
    LoginThrottle,
    require_secure_admin_password,
    verify_admin_credentials,
)

# 配置
driver = get_driver()

def _get_or_create_jwt_secret():
    """获取或自动生成 JWT 密钥"""
    # 先尝试从配置获取
    configured_secret = getattr(driver.config, "jwt_secret", None)
    if configured_secret and configured_secret != "your_secret_key_here_change_in_production":
        return str(configured_secret)

    # 没有配置，尝试从缓存文件读取（保证重启后密钥一致）
    secret_file = Path(__file__).parent.parent.parent.parent / "data" / ".jwt_secret"
    if secret_file.exists():
        saved_secret = secret_file.read_text(encoding="utf-8").strip()
        if saved_secret:
            return saved_secret

    # 首次运行，自动生成并保存
    new_secret = secrets.token_urlsafe(32)
    secret_file.parent.mkdir(parents=True, exist_ok=True)
    secret_file.write_text(new_secret, encoding="utf-8")
    try:
        os.chmod(secret_file, 0o600)
    except OSError:
        pass
    return new_secret

SECRET_KEY = _get_or_create_jwt_secret()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(getattr(driver.config, "jwt_expire_minutes", 1440))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
login_throttle = LoginThrottle()

router = APIRouter()

# ==================== 模型定义 ====================

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

# ==================== 工具函数 ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# ==================== 依赖注入 ====================

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 模拟用户对象
    user = User(username=username, disabled=False)
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# ==================== 路由接口 ====================

@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    登录获取 Token
    """
    client_key = request.client.host if request.client else "unknown"
    if login_throttle.is_limited(client_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
        )

    try:
        admin_password = require_secure_admin_password(
            getattr(driver.config, "web_admin_password", None)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Web administrator password is not securely configured.",
        ) from exc

    if not verify_admin_credentials(
        form_data.username,
        form_data.password,
        admin_password,
    ):
        login_throttle.record_failure(client_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    login_throttle.reset(client_key)
    user = User(username="admin")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
