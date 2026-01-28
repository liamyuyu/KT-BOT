"""
搜索 API 路由
Story 4.5 Phase 4
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from src.services.search import DocumentSearchEngine, SearchQuery, SearchResponse
from src.services.search.models import SearchMethod
from src.core.rag.retriever import get_vector_retriever, get_hybrid_retriever

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


# ========================================================================
# 依赖注入
# ========================================================================

def get_search_engine() -> DocumentSearchEngine:
    """获取搜索引擎实例"""
    vector_retriever = get_vector_retriever()
    hybrid_retriever = get_hybrid_retriever()

    return DocumentSearchEngine(
        vector_retriever=vector_retriever,
        bm25_retriever=None,  # 暂不支持独立BM25
        hybrid_retriever=hybrid_retriever
    )


# ========================================================================
# API 端点
# ========================================================================

@router.post("/documents", response_model=Dict[str, Any])
async def search_documents(
    query: SearchQuery,
    search_engine: DocumentSearchEngine = Depends(get_search_engine)
) -> Dict[str, Any]:
    """
    搜索文档

    支持向量搜索、BM25搜索和混合搜索

    Args:
        query: 搜索查询参数
        search_engine: 搜索引擎实例

    Returns:
        搜索结果
    """
    try:
        logger.info(
            f"Document search: query='{query.query}', method={query.method}, "
            f"page={query.page}, page_size={query.page_size}"
        )

        response = await search_engine.search(query)

        return {
            "data": response.dict(),
            "message": f"Found {response.total} results"
        }

    except ValueError as e:
        logger.error(f"Invalid search request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/methods")
async def list_search_methods() -> Dict[str, Any]:
    """
    获取支持的搜索方法列表

    Returns:
        搜索方法列表
    """
    return {
        "data": {
            "methods": [
                {
                    "value": SearchMethod.VECTOR.value,
                    "label": "向量搜索",
                    "description": "基于语义相似度的搜索"
                },
                {
                    "value": SearchMethod.BM25.value,
                    "label": "全文搜索",
                    "description": "基于关键词匹配的搜索"
                },
                {
                    "value": SearchMethod.HYBRID.value,
                    "label": "混合搜索",
                    "description": "结合向量和全文搜索"
                }
            ],
            "default": SearchMethod.HYBRID.value
        },
        "message": "Search methods listed successfully"
    }


@router.get("/stats")
async def get_search_stats() -> Dict[str, Any]:
    """
    获取搜索统计信息

    Returns:
        搜索统计数据
    """
    # 简化实现，返回占位数据
    return {
        "data": {
            "total_searches": 0,
            "popular_queries": [],
            "avg_search_time_ms": 0
        },
        "message": "Search stats retrieved successfully"
    }
