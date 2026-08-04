# -*- coding: utf-8 -*-
"""
敏感词管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Keyword
from src.database.crud import add_keyword, remove_keyword

router = APIRouter()


async def get_db():
    async with get_session() as session:
        yield session


class KeywordCreate(BaseModel):
    word: str = Field(min_length=1, max_length=100)
    category: str = Field(default="通用", min_length=1, max_length=50)
    risk_level: int = Field(default=1, ge=1, le=5)


class KeywordUpdate(BaseModel):
    category: Optional[str] = Field(default=None, min_length=1, max_length=50)
    risk_level: Optional[int] = Field(default=None, ge=1, le=5)
    is_active: Optional[bool] = None


@router.get("/list")
async def list_keywords(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db)
):
    """获取敏感词列表"""
    offset = (page - 1) * size

    result = await session.execute(
        select(Keyword).offset(offset).limit(size)
    )

    keywords = [
        {
            "id": kw.id,
            "word": kw.word,
            "category": kw.category,
            "risk_level": kw.risk_level,
            "is_active": kw.is_active,
            "created_at": kw.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for kw in result.scalars()
    ]

    return {"keywords": keywords, "page": page, "size": size}


@router.post("/add")
async def add_new_keyword(
    data: KeywordCreate,
    session: AsyncSession = Depends(get_db)
):
    """添加敏感词"""
    success, message = await add_keyword(
        session, data.word, data.category, data.risk_level
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message}


@router.delete("/{keyword_id}")
async def delete_keyword(
    keyword_id: int,
    session: AsyncSession = Depends(get_db)
):
    """删除敏感词"""
    result = await session.execute(
        select(Keyword).where(Keyword.id == keyword_id)
    )
    keyword = result.scalar_one_or_none()

    if not keyword:
        raise HTTPException(status_code=404, detail="敏感词不存在")

    success, message = await remove_keyword(session, keyword.word)
    return {"success": success, "message": message}


@router.put("/{keyword_id}")
async def update_keyword(
    keyword_id: int,
    data: KeywordUpdate,
    session: AsyncSession = Depends(get_db)
):
    """更新敏感词"""
    result = await session.execute(
        select(Keyword).where(Keyword.id == keyword_id)
    )
    keyword = result.scalar_one_or_none()

    if not keyword:
        raise HTTPException(status_code=404, detail="敏感词不存在")

    if data.category is not None:
        keyword.category = data.category
    if data.risk_level is not None:
        keyword.risk_level = data.risk_level
    if data.is_active is not None:
        keyword.is_active = data.is_active

    await session.commit()
    return {"success": True, "message": "更新成功"}
