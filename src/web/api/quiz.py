# -*- coding: utf-8 -*-
"""
题库管理 API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import List, Optional

from nonebot import require
require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import QuizQuestion

router = APIRouter()


async def get_db():
    async with get_session() as session:
        yield session


class QuestionCreate(BaseModel):
    category: str = Field(min_length=1, max_length=50)
    question: str = Field(min_length=1, max_length=1000)
    options: List[str] = Field(min_items=2, max_items=8)
    answer: str = Field(min_length=1, max_length=200)
    explanation: str = Field(default="", max_length=2000)
    difficulty: int = Field(default=1, ge=1, le=5)

    @validator("options")
    def validate_options(cls, value: List[str]) -> List[str]:
        cleaned = [item.strip() for item in value]
        if any(not item or len(item) > 500 for item in cleaned):
            raise ValueError("each option must contain 1-500 characters")
        return cleaned


@router.get("/list")
async def list_questions(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = Query(default=None, max_length=50),
    session: AsyncSession = Depends(get_db)
):
    """获取题目列表"""
    offset = (page - 1) * size

    query = select(QuizQuestion)
    if category:
        query = query.where(QuizQuestion.category == category)

    result = await session.execute(query.offset(offset).limit(size))

    questions = [
        {
            "id": q.id,
            "category": q.category,
            "question": q.question[:50] + "..." if len(q.question) > 50 else q.question,
            "answer": q.answer,
            "difficulty": q.difficulty,
            "is_active": q.is_active
        }
        for q in result.scalars()
    ]

    return {"questions": questions, "page": page, "size": size}


@router.get("/categories")
async def get_categories(session: AsyncSession = Depends(get_db)):
    """获取题目分类"""
    result = await session.execute(
        select(
            QuizQuestion.category,
            func.count(QuizQuestion.id).label('count')
        ).group_by(QuizQuestion.category)
    )

    categories = [
        {"category": row.category, "count": row.count}
        for row in result
    ]

    return {"categories": categories}


@router.post("/add")
async def add_question(
    data: QuestionCreate,
    session: AsyncSession = Depends(get_db)
):
    """添加题目"""
    question = QuizQuestion(
        category=data.category,
        question=data.question,
        options=data.options,
        answer=data.answer,
        explanation=data.explanation,
        difficulty=data.difficulty
    )

    session.add(question)
    await session.commit()

    return {"success": True, "id": question.id}


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    session: AsyncSession = Depends(get_db)
):
    """删除题目"""
    result = await session.execute(
        select(QuizQuestion).where(QuizQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()

    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    question.is_active = False
    await session.commit()

    return {"success": True, "message": "已删除"}
