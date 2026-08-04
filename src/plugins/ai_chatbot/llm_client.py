# -*- coding: utf-8 -*-
"""
大模型客户端
封装 OpenAI 兼容 API 调用
"""

from typing import List, Dict
import httpx
from nonebot import logger


class LLMClient:
    """大模型客户端"""

    def __init__(
        self,
        api_key: str,
        api_base: str,
        model: str,
        timeout: int = 30
    ):
        """
        初始化客户端

        Args:
            api_key: API 密钥
            api_base: API 基础地址
            model: 模型名称
            timeout: 超时时间
        """
        self.api_key = api_key
        self.api_base = api_base.rstrip('/')
        self.model = model
        self.timeout = timeout

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        调用聊天接口

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            AI 回复内容

        Raises:
            Exception: API 调用失败
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return content.strip()

        except httpx.TimeoutException:
            logger.error("LLM API 请求超时")
            raise Exception("请求超时，请稍后重试")
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API 请求失败: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API 请求失败: {e.response.status_code}")
        except KeyError as e:
            logger.error(f"LLM API 响应格式错误: {e}")
            raise Exception("API 响应格式异常")
        except Exception as e:
            logger.error(f"LLM API 调用异常: {e}")
            raise
