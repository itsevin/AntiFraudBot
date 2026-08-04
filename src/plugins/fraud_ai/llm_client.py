# -*- coding: utf-8 -*-
"""
大模型 API 客户端
支持 DeepSeek、通义千问、OpenAI 等兼容接口
"""

import httpx
import json
from typing import Optional

from nonebot import logger
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.crud import log_ai_analysis
from .prompt_template import get_fraud_analysis_prompt


async def analyze_fraud(
    text: str,
    api_key: str,
    api_base: str,
    model: str,
    session: AsyncSession,
    user_id: str,
    group_id: Optional[str] = None,
    timeout: int = 30,
    max_tokens: int = 1000
) -> dict:
    """
    调用大模型分析诈骗话术

    Args:
        text: 待分析文本
        api_key: API 密钥
        api_base: API 基础地址
        model: 模型名称
        session: 数据库会话
        user_id: 用户ID
        group_id: 群ID
        timeout: 超时时间
        max_tokens: 最大 Token

    Returns:
        分析结果字典
    """
    # 构建请求
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = get_fraud_analysis_prompt(text)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt["system"]},
            {"role": "user", "content": prompt["user"]}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3  # 低温度，更稳定的输出
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # 尝试提取思维链 (DeepSeek R1 style <think>...</think>)
            reasoning_trace = None
            if "<think>" in content and "</think>" in content:
                try:
                    trace_start = content.index("<think>") + 7
                    trace_end = content.index("</think>")
                    reasoning_trace = content[trace_start:trace_end].strip()
                    # 移除思维链部分，只保留最终回复给 frontend/client 解析
                    # content = content.split("</think>")[1].strip()
                    #注: 暂时保留全文给 _parse_ai_response 处理，或者这里仅提取 trace 存库
                except:
                    pass

            # 解析 AI 返回的 JSON
            result = _parse_ai_response(content)

            # 记录分析日志
            await log_ai_analysis(
                session=session,
                user_id=user_id,
                input_text=text,
                risk_level=result.get("risk_level", "低危"),
                fraud_type=result.get("fraud_type"),
                analysis_result=content,
                model_used=model,
                group_id=group_id,
                reasoning_trace=reasoning_trace  # 新增思维链字段
            )

            return result

    except httpx.TimeoutException:
        logger.error("AI 请求超时")
        raise Exception("请求超时，请稍后重试")
    except httpx.HTTPStatusError as e:
        logger.error(f"AI 请求失败: {e.response.status_code}")
        raise Exception(f"API 请求失败: {e.response.status_code}")
    except Exception as e:
        logger.error(f"AI 分析异常: {e}")
        raise


def _parse_ai_response(content: str) -> dict:
    """
    解析 AI 返回的内容
    尝试解析 JSON，失败则进行文本解析
    """
    # 尝试直接解析 JSON
    try:
        # 查找 JSON 块
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
            return json.loads(json_str)
        elif "{" in content and "}" in content:
            # 提取第一个完整的 JSON 对象
            start = content.index("{")
            end = content.rindex("}") + 1
            json_str = content[start:end]
            return json.loads(json_str)
    except (json.JSONDecodeError, IndexError, ValueError):
        pass

    # 文本解析回退
    result = {
        "risk_level": "低危",
        "fraud_type": "未识别",
        "features": "无法解析AI返回内容",
        "advice": "请保持警惕，如有疑问请拨打110咨询"
    }

    # 简单关键词匹配
    content_lower = content.lower()
    if "高危" in content or "high" in content_lower:
        result["risk_level"] = "高危"
    elif "中危" in content or "medium" in content_lower:
        result["risk_level"] = "中危"

    # 诈骗类型识别
    fraud_types = [
        "刷单返利", "虚假投资", "冒充公检法", "杀猪盘",
        "网络贷款", "冒充客服", "虚假中奖", "冒充领导"
    ]
    for ft in fraud_types:
        if ft in content:
            result["fraud_type"] = ft
            break

    result["features"] = content[:300] + "..." if len(content) > 300 else content

    return result
