# -*- coding: utf-8 -*-
"""
答题会话管理
处理答题流程和状态
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from nonebot import on_message, require
from nonebot.adapters.onebot.v11 import Event, GroupMessageEvent, PrivateMessageEvent, Bot
from nonebot.params import EventPlainText
from nonebot.matcher import Matcher

require("nonebot_plugin_orm")
from nonebot_plugin_orm import async_scoped_session

from src.database.models import QuizQuestion
from src.database.crud import add_score, get_or_create_user_score


@dataclass
class QuizSession:
    """答题会话"""
    user_id: str
    group_id: Optional[str]
    questions: List[QuizQuestion]
    current_index: int = 0
    correct_count: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    @property
    def is_finished(self) -> bool:
        return self.current_index >= len(self.questions)

    @property
    def current_question(self) -> Optional[QuizQuestion]:
        if self.is_finished:
            return None
        return self.questions[self.current_index]

    @property
    def is_timeout(self) -> bool:
        return datetime.now() - self.start_time > timedelta(minutes=5)


# 全局会话存储 {user_id: QuizSession}
_quiz_sessions: Dict[str, QuizSession] = {}


def get_quiz_state(user_id: str) -> Optional[QuizSession]:
    """获取用户的答题状态"""
    session = _quiz_sessions.get(user_id)
    if session and (session.is_finished or session.is_timeout):
        del _quiz_sessions[user_id]
        return None
    return session


async def start_quiz_session(
    user_id: str,
    group_id: Optional[str],
    questions: List[QuizQuestion]
) -> str:
    """开始一个新的答题会话"""
    session = QuizSession(
        user_id=user_id,
        group_id=group_id,
        questions=questions
    )
    _quiz_sessions[user_id] = session

    return _format_question(session)


def _format_question(session: QuizSession) -> str:
    """格式化题目显示"""
    q = session.current_question
    if not q:
        return "❌ 题目加载失败"

    # 解析选项
    import json
    try:
        options = json.loads(q.options) if isinstance(q.options, str) else q.options
    except:
        options = ["A. 选项加载失败"]

    options_text = "\n".join(options)

    return f"""
📚 【反诈知识问答】第 {session.current_index + 1}/{len(session.questions)} 题

🏷️ 类型：{q.category}

❓ {q.question}

{options_text}

💡 请直接回复 A/B/C/D 作答
⏱️ 答题时限：5分钟
""".strip()


# ==================== 答题消息监听 ====================
quiz_answer = on_message(priority=1, block=False)


@quiz_answer.handle()
async def handle_answer(
    bot: Bot,
    event: Event,
    session: async_scoped_session,
    matcher: Matcher,
    msg: str = EventPlainText()
):
    """处理用户答案"""
    user_id = event.get_user_id()
    quiz_session = get_quiz_state(user_id)

    if not quiz_session:
        return  # 没有进行中的答题

    # 检查是否为有效答案
    answer = msg.strip().upper()
    if answer not in ["A", "B", "C", "D"]:
        return  # 不是答案格式，忽略

    # 阻止消息继续传播
    matcher.stop_propagation()

    # 检查答案
    current_q = quiz_session.current_question
    is_correct = answer == current_q.answer.upper()

    if is_correct:
        quiz_session.correct_count += 1
        result_text = "✅ 回答正确！"
    else:
        result_text = f"❌ 回答错误！正确答案是 {current_q.answer}"

    # 显示解析
    explanation = f"\n📖 解析：{current_q.explanation}"

    # 移动到下一题
    quiz_session.current_index += 1

    if quiz_session.is_finished:
        # 答题结束，计算得分
        total_correct = quiz_session.correct_count
        total_questions = len(quiz_session.questions)
        earned_score = total_correct * 10  # 每题10分

        try:
            # 更新积分
            user_score = await get_or_create_user_score(
                session, user_id, quiz_session.group_id
            )
            user_score.score += earned_score
            user_score.quiz_count += total_questions
            user_score.correct_count += total_correct
            user_score.last_quiz = datetime.now()
            await session.commit()

            score_msg = f"🏆 当前总积分：{user_score.score} 分"
        except Exception as e:
            from nonebot import logger
            logger.error(f"更新积分失败: {e}")
            score_msg = "⚠️ 积分更新遇到异常，请联系管理员"

        # 清理会话
        del _quiz_sessions[user_id]

        # 发送结算消息
        finish_msg = f"""
{result_text}
{explanation}

🎉 【答题结束】

📊 本轮成绩：{total_correct}/{total_questions} 正确
💰 获得积分：+{earned_score} 分
{score_msg}

感谢参与反诈知识问答！
""".strip()

        if isinstance(event, GroupMessageEvent):
            await bot.send_group_msg(group_id=event.group_id, message=finish_msg)
        else:
            await bot.send_private_msg(user_id=int(user_id), message=finish_msg)
    else:
        # 显示下一题
        next_question = _format_question(quiz_session)
        response = f"{result_text}\n{explanation}\n\n{'='*30}\n\n{next_question}"

        from nonebot import get_bot
        bot = get_bot()
        if isinstance(event, GroupMessageEvent):
            await bot.send_group_msg(group_id=event.group_id, message=response)
        else:
            await bot.send_private_msg(user_id=int(user_id), message=response)
