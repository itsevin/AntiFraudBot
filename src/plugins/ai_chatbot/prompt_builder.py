# -*- coding: utf-8 -*-
"""
提示词构建器
动态构建大模型提示词
"""

from typing import List, Optional, Dict


class PromptBuilder:
    """动态提示词构建器"""

    @staticmethod
    def build_chatbot_prompt(
        user_question: str,
        context_history: List[dict],
        rag_results: List[dict],
        group_stats: Optional[dict] = None
    ) -> dict:
        """
        构建聊天机器人提示词

        Args:
            user_question: 用户当前问题
            context_history: 对话历史
            rag_results: RAG 检索结果
            group_stats: 群组统计数据

        Returns:
            包含 messages 的字典
        """

        # 1. 构建知识库上下文
        rag_context = ""
        if rag_results:
            rag_context = "\n【相关知识参考】\n"
            for i, result in enumerate(rag_results, 1):
                rag_context += f"{i}. {result['content']}\n"

        # 2. 构建群组数据洞察
        group_insight = ""
        if group_stats and group_stats.get("total_count", 0) > 0:
            top_types_str = "、".join(group_stats.get("top_types", [])) or "暂无"
            group_insight = f"""
【本群数据洞察】
- 近30天拦截诈骗消息: {group_stats.get('total_count', 0)} 条
- 高发诈骗类型: {top_types_str}
- 群成员反诈意识评分: {group_stats.get('avg_score', 60)}/100
"""

        # 3. 构建系统提示词
        system_prompt = f"""你是一位专业、友好的反诈骗咨询助手，名为「反诈卫士🛡️」。

【你的能力】
1. 回答用户关于诈骗识别、防范技巧、案例分析的问题
2. 分析可疑信息、链接、话术是否为诈骗
3. 提供针对性的防护建议和应对策略
4. 科普常见诈骗手法和最新诈骗趋势

{rag_context}

{group_insight}

【对话原则】
- 专业但不生硬，使用口语化、易懂的表达方式
- 回答简洁明了，重点突出，适当分点列出
- 适当使用 emoji 增强可读性和亲和力（如 ✅、⚠️、💡、🔍）
- 如遇到不确定的问题，诚实告知并建议拨打 96110（反诈专线）或 110 咨询
- 多鼓励用户提高警惕，强调"天上不会掉馅饼"的原则
- 对于明显的诈骗特征，要明确警示，态度坚决

【回答格式】
- 严禁使用 Markdown 格式（不要使用 **加粗**、# 标题等）
- 使用纯文本格式，适当换行
- 可以使用 emoji 增强可读性（如 ✅、⚠️、💡）
- 每次回答控制在 200 字以内，避免冗长

【重要提示】
- 你是反诈专家，要有专业性和权威性
- 涉及资金、个人信息的问题，务必提醒用户警惕
- 遇到典型诈骗话术，要明确指出并解释套路
"""

        # 4. 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]

        # 5. 添加历史对话（最多保留最近几轮）
        messages.extend(context_history)

        # 6. 添加当前问题
        messages.append({"role": "user", "content": user_question})

        return {
            "messages": messages,
            "system": system_prompt,
            "user": user_question
        }

    @staticmethod
    def build_simple_prompt(user_question: str) -> dict:
        """
        构建简单提示词（无上下文）

        Args:
            user_question: 用户问题

        Returns:
            包含 messages 的字典
        """
        system_prompt = """你是反诈卫士🛡️，一位专业的反诈骗咨询助手。
请用简洁、友好的方式回答用户的反诈问题，200字以内。
如不确定，建议用户拨打 96110 反诈专线。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ]

        return {
            "messages": messages,
            "system": system_prompt,
            "user": user_question
        }
