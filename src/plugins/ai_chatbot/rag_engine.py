# -*- coding: utf-8 -*-
"""
简化版 RAG 引擎
基于关键词匹配的知识库检索
"""

from typing import List, Optional
from pathlib import Path
from nonebot import logger


class SimpleRAGEngine:
    """简化版 RAG 引擎（基于关键词匹配）"""

    def __init__(self, knowledge_dir: str = "source"):
        """
        初始化 RAG 引擎

        Args:
            knowledge_dir: 知识库根目录
        """
        self.knowledge_base: List[dict] = []
        self._load_knowledge(knowledge_dir)

    def _load_knowledge(self, knowledge_dir: str):
        """加载知识库"""
        try:
            base_path = Path(knowledge_dir)

        # 1. 加载敏感词库
            keyword_file = base_path / "keyword.txt"
            if keyword_file.exists():
                content = keyword_file.read_text(encoding="utf-8")
                lines = [line.strip() for line in content.split("\n") if line.strip()]

                # 动态构建分类字典 {分类名: [关键词列表]}
                fraud_types = {}

                for line in lines:
                    if "|" in line:
                        parts = line.split("|", 1)
                        kw = parts[0].strip()
                        category = parts[1].strip()
                    else:
                        kw = line
                        category = "通用风险"

                    if not kw: continue

                    if category not in fraud_types:
                        fraud_types[category] = []
                    fraud_types[category].append(kw)

                # 转换为知识条目
                for fraud_type, type_keywords in fraud_types.items():
                    self.knowledge_base.append({
                        "type": "fraud_keywords",
                        "fraud_type": fraud_type,
                        "keywords": set(type_keywords),
                        "content": f"{fraud_type}常见关键词：{', '.join(type_keywords[:10])}" + \
                                 ("..." if len(type_keywords) > 10 else "")
                    })

                logger.info(f"加载了 {len(lines)} 个敏感关键词，分为 {len(fraud_types)} 类")

            # 2. 加载反诈知识点（占位符，未来扩展 OCR）
            knowledge_path = base_path / "knowledge"
            if knowledge_path.exists() and knowledge_path.is_dir():
                image_count = len(list(knowledge_path.glob("*.png"))) + len(list(knowledge_path.glob("*.jpg")))
                if image_count > 0:
                    self.knowledge_base.append({
                        "type": "knowledge_images",
                        "content": f"知识库包含 {image_count} 张反诈知识图片（OCR待实现）",
                        "keywords": set()
                    })
                    logger.info(f"发现 {image_count} 张反诈知识图片")

            # 3. 添加通用反诈建议
            self.knowledge_base.append({
                "type": "general_advice",
                "content": """通用防诈建议：
1. 不轻信陌生人的任何要求
2. 不透露个人信息、验证码、银行卡密码
3. 不点击不明链接，不扫描可疑二维码
4. 不向陌生账户转账汇款
5. 遇到可疑情况，立即拨打 96110 反诈专线或 110 报警""",
                "keywords": set(["建议", "如何", "防范", "怎么办", "怎样"])
            })

            logger.success(f"RAG 引擎初始化完成，知识库条目数：{len(self.knowledge_base)}")

        except Exception as e:
            logger.error(f"加载知识库失败: {e}")
            # 即使失败也添加基本建议
            self.knowledge_base.append({
                "type": "general_advice",
                "content": "如遇可疑情况，请立即拨打 96110 反诈专线或 110 报警",
                "keywords": set()
            })

    async def search(self, query: str, top_k: int = 3) -> List[dict]:
        """
        检索相关知识

        Args:
            query: 用户查询
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        results = []
        query_lower = query.lower()

        for item in self.knowledge_base:
            score = 0
            matched_keywords = []

            # 1. 关键词匹配评分
            if item["type"] == "fraud_keywords":
                for kw in item["keywords"]:
                    if kw in query:
                        matched_keywords.append(kw)
                        score += 10  # 每个关键词 +10 分

                if matched_keywords:
                    results.append({
                        "content": f"⚠️ 检测到 {item['fraud_type']} 相关词汇：{', '.join(matched_keywords[:5])}",
                        "type": item["fraud_type"],
                        "score": score,
                        "keywords": matched_keywords
                    })

            # 2. 通用建议匹配
            elif item["type"] == "general_advice":
                for kw in item["keywords"]:
                    if kw in query_lower:
                        score += 5

                if score > 0 or len(results) == 0:  # 如果没有其他匹配，返回通用建议
                    results.append({
                        "content": item["content"],
                        "type": "general",
                        "score": score if score > 0 else 1
                    })

        # 3. 按分数排序
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

        # 4. 返回 Top-K
        return results[:top_k] if results else []

    async def get_fraud_type_info(self, fraud_type: str) -> Optional[dict]:
        """获取特定诈骗类型的信息"""
        for item in self.knowledge_base:
            if item.get("fraud_type") == fraud_type:
                return item
        return None


# 全局单例
_rag_engine_instance: Optional[SimpleRAGEngine] = None


def get_rag_engine(knowledge_dir: str = "source") -> SimpleRAGEngine:
    """获取 RAG 引擎单例"""
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = SimpleRAGEngine(knowledge_dir)
    return _rag_engine_instance
