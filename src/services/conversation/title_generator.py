"""
对话标题生成器
Story 5.1 Phase 2: 对话标题自动生成
"""

import logging
import re
from typing import Optional, List
from collections import Counter

import jieba
import jieba.analyse

from .models import TitleGenerationMethod, TitleGenerationConfig

logger = logging.getLogger(__name__)


class TitleGenerator:
    """
    对话标题生成器

    支持两种生成方式：
    1. 关键词提取（使用 jieba 的 TF-IDF 和 TextRank）
    2. LLM 生成（调用大模型生成标题）
    """

    def __init__(self):
        """初始化标题生成器"""
        # 初始化 jieba
        jieba.setLogLevel(logging.WARNING)
        logger.info("TitleGenerator initialized")

        # 停用词列表
        self.stopwords = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那", "能",
            "对", "这个", "来", "他", "时候", "如何", "什么", "怎么", "为什么"
        }

    def generate_title(
        self,
        message_content: str,
        config: Optional[TitleGenerationConfig] = None
    ) -> str:
        """
        生成对话标题

        Args:
            message_content: 消息内容（通常是对话的第一条消息）
            config: 标题生成配置

        Returns:
            生成的标题
        """
        if config is None:
            config = TitleGenerationConfig()

        # 清理文本
        cleaned_text = self._clean_text(message_content)

        if not cleaned_text:
            return "新对话"

        # 根据配置选择生成方法
        if config.method == TitleGenerationMethod.KEYWORD:
            title = self._generate_by_keyword(cleaned_text, config)
        elif config.method == TitleGenerationMethod.LLM:
            # LLM 生成（暂未实现，后续可扩展）
            logger.warning("LLM title generation not implemented, falling back to keyword extraction")
            title = self._generate_by_keyword(cleaned_text, config)
        else:  # AUTO
            # 自动选择：优先使用关键词提取
            title = self._generate_by_keyword(cleaned_text, config)

        # 截断标题长度
        if len(title) > config.max_length:
            title = title[:config.max_length] + "..."

        logger.info(f"Generated title: {title}")
        return title

    def _generate_by_keyword(
        self,
        text: str,
        config: TitleGenerationConfig
    ) -> str:
        """
        通过关键词提取生成标题

        Args:
            text: 文本内容
            config: 生成配置

        Returns:
            生成的标题
        """
        # 1. 尝试提取问句
        question = self._extract_question(text)
        if question:
            return question

        # 2. 使用 TF-IDF 提取关键词
        keywords_tfidf = jieba.analyse.extract_tags(
            text,
            topK=config.keyword_count,
            withWeight=False
        )

        # 3. 使用 TextRank 提取关键词
        keywords_textrank = jieba.analyse.textrank(
            text,
            topK=config.keyword_count,
            withWeight=False
        )

        # 4. 合并关键词并去重
        all_keywords = keywords_tfidf + keywords_textrank

        # 5. 过滤停用词
        filtered_keywords = [
            kw for kw in all_keywords
            if kw not in self.stopwords and len(kw) > 1
        ]

        # 6. 去重并保持顺序
        unique_keywords = []
        seen = set()
        for kw in filtered_keywords:
            if kw not in seen:
                unique_keywords.append(kw)
                seen.add(kw)

        # 7. 取前 N 个关键词
        top_keywords = unique_keywords[:config.keyword_count]

        if not top_keywords:
            # 如果没有提取到关键词，使用文本开头
            return text[:30] + ("..." if len(text) > 30 else "")

        # 8. 生成标题
        title = "关于 " + "、".join(top_keywords)
        return title

    def _extract_question(self, text: str) -> Optional[str]:
        """
        提取问句作为标题

        Args:
            text: 文本内容

        Returns:
            问句文本，如果没有问句则返回 None
        """
        # 分句
        sentences = re.split(r'[。！？\n]', text)

        # 查找问句
        for sentence in sentences:
            sentence = sentence.strip()
            # 检查是否包含疑问词或问号
            if any(word in sentence for word in ['如何', '怎么', '为什么', '什么', '哪', '谁', '吗', '呢', '？']):
                # 清理句子
                cleaned = sentence.replace('?', '').replace('？', '').strip()
                if 10 <= len(cleaned) <= 100:  # 长度合理的问句
                    return cleaned

        return None

    def _clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)

        # 移除特殊字符（保留中文、英文、数字、常用标点）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？、；：""''（）《》\s]', '', text)

        return text.strip()

    def generate_title_from_keywords(self, keywords: List[str]) -> str:
        """
        根据给定的关键词生成标题

        Args:
            keywords: 关键词列表

        Returns:
            生成的标题
        """
        if not keywords:
            return "新对话"

        # 过滤空关键词
        filtered = [kw.strip() for kw in keywords if kw.strip()]

        if not filtered:
            return "新对话"

        # 生成标题
        title = "关于 " + "、".join(filtered[:5])
        return title

    def extract_keywords(
        self,
        text: str,
        top_k: int = 5
    ) -> List[str]:
        """
        提取文本关键词

        Args:
            text: 文本内容
            top_k: 返回的关键词数量

        Returns:
            关键词列表
        """
        cleaned_text = self._clean_text(text)

        if not cleaned_text:
            return []

        # 使用 TF-IDF 提取
        keywords = jieba.analyse.extract_tags(
            cleaned_text,
            topK=top_k,
            withWeight=False
        )

        # 过滤停用词
        filtered = [
            kw for kw in keywords
            if kw not in self.stopwords and len(kw) > 1
        ]

        return filtered[:top_k]
