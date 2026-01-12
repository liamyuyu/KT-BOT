"""
Retriever Module
检索器模块：提供各种检索策略的实现
"""

from .base import BaseRetriever
from .vector import VectorRetriever, get_vector_retriever

__all__ = [
    "BaseRetriever",
    "VectorRetriever",
    "get_vector_retriever",
]
