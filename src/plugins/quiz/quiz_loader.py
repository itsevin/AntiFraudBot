# -*- coding: utf-8 -*-
"""
题库加载器
从 JSON 文件加载题目到数据库
"""

import json
from pathlib import Path

from nonebot import logger, require

require("nonebot_plugin_orm")
from nonebot_plugin_orm import get_session
from sqlalchemy import select

from src.database.models import QuizQuestion


async def load_quiz_bank():
    """加载题库到数据库"""
    quiz_file = Path("source/quiz_bank.json")
    if not quiz_file.exists():
        logger.warning("题库文件 source/quiz_bank.json 不存在")
        return 0

    async with get_session() as session:
        with open(quiz_file, "r", encoding="utf-8") as f:
            questions = json.load(f)

        loaded = 0
        for q in questions:
            # 检查是否已存在
            result = await session.execute(
                select(QuizQuestion).where(
                    QuizQuestion.question == q["question"]
                )
            )
            if result.scalar_one_or_none():
                continue

            session.add(QuizQuestion(
                category=q.get("category", "通用"),
                question=q["question"],
                options=q["options"],
                answer=q["answer"],
                explanation=q.get("explanation", ""),
                difficulty=q.get("difficulty", 1)
            ))
            loaded += 1

        await session.commit()
        logger.info(f"成功加载 {loaded} 道题目到数据库")
        return loaded
