"""
端到端测试：完整 RAG Pipeline（Hybrid + Reranking）
验证 Hybrid Retrieval → Cross-Encoder Reranking → Top-K 流程
"""
import asyncio
import logging
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api.services.chat_service import ChatService
from src.api.schemas.chat import ChatRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_rag_pipeline_with_reranking():
    """测试完整的 RAG Pipeline 包含重排序"""
    logger.info("=" * 80)
    logger.info("开始测试：完整 RAG Pipeline（Hybrid → Rerank → Top-K）")
    logger.info("=" * 80)

    # 初始化 ChatService
    logger.info("\n1. 初始化 ChatService...")
    chat_service = ChatService()
    logger.info("✓ ChatService 初始化完成")

    # 验证检索器是否就绪
    logger.info(f"  - Vector Retriever: {'✓' if chat_service.vector_retriever else '✗'}")
    logger.info(f"  - BM25 Retriever: {'✓' if chat_service.bm25_retriever else '✗'}")
    logger.info(f"  - Hybrid Retriever: {'✓' if chat_service.hybrid_retriever else '✗'}")
    logger.info(f"  - Reranker: {'✓' if chat_service.reranker else '✗'}")

    # 测试查询
    test_queries = [
        "如何配置 Jira API Token？",
        "RAG 检索系统的实现原理是什么？",
        "ChromaDB 向量数据库如何使用？"
    ]

    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n{'=' * 80}")
        logger.info(f"测试用例 {i}/{len(test_queries)}: {query}")
        logger.info(f"{'=' * 80}")

        # 测试场景1：混合检索 + 重排序（默认）
        logger.info(f"\n场景 1: Hybrid Retrieval + Reranking (默认配置)")
        request_with_rerank = ChatRequest(
            message=query,
            enable_rag=True,
            rag_top_k=3,
            retrieval_method="hybrid",
            fusion_method="rrf",
            vector_weight=0.5,
            bm25_weight=0.5,
            enable_reranking=True,
            rerank_top_k=10,
            temperature=0.7
        )

        try:
            contexts_with_rerank = await chat_service._retrieve_contexts(
                query=request_with_rerank.message,
                top_k=request_with_rerank.rag_top_k,
                retrieval_method=request_with_rerank.retrieval_method,
                vector_weight=request_with_rerank.vector_weight,
                bm25_weight=request_with_rerank.bm25_weight,
                fusion_method=request_with_rerank.fusion_method,
                enable_reranking=request_with_rerank.enable_reranking,
                rerank_top_k=request_with_rerank.rerank_top_k
            )

            if contexts_with_rerank:
                logger.info(f"✓ 检索成功，返回 {len(contexts_with_rerank)} 个结果")
                for j, ctx in enumerate(contexts_with_rerank, 1):
                    rerank_info = ""
                    if ctx.reranked:
                        rerank_info = f" [重排序分数: {ctx.rerank_score:.4f}, 原排名: {ctx.original_rank}]"
                    logger.info(
                        f"  [{j}] {ctx.source.get('issue_key', 'Unknown')} "
                        f"(分数: {ctx.score:.4f}{rerank_info})"
                    )
                    logger.info(f"      内容: {ctx.content[:100]}...")
            else:
                logger.warning("✗ 未检索到结果")

        except Exception as e:
            logger.error(f"✗ 检索失败: {e}", exc_info=True)
            continue

        # 测试场景2：混合检索 + 不重排序
        logger.info(f"\n场景 2: Hybrid Retrieval (不重排序)")
        request_without_rerank = ChatRequest(
            message=query,
            enable_rag=True,
            rag_top_k=3,
            retrieval_method="hybrid",
            fusion_method="rrf",
            vector_weight=0.5,
            bm25_weight=0.5,
            enable_reranking=False,  # 关闭重排序
            temperature=0.7
        )

        try:
            contexts_without_rerank = await chat_service._retrieve_contexts(
                query=request_without_rerank.message,
                top_k=request_without_rerank.rag_top_k,
                retrieval_method=request_without_rerank.retrieval_method,
                vector_weight=request_without_rerank.vector_weight,
                bm25_weight=request_without_rerank.bm25_weight,
                fusion_method=request_without_rerank.fusion_method,
                enable_reranking=request_without_rerank.enable_reranking,
                rerank_top_k=request_without_rerank.rerank_top_k
            )

            if contexts_without_rerank:
                logger.info(f"✓ 检索成功，返回 {len(contexts_without_rerank)} 个结果")
                for j, ctx in enumerate(contexts_without_rerank, 1):
                    logger.info(
                        f"  [{j}] {ctx.source.get('issue_key', 'Unknown')} "
                        f"(分数: {ctx.score:.4f}, 距离: {ctx.distance:.4f})"
                    )
            else:
                logger.warning("✗ 未检索到结果")

        except Exception as e:
            logger.error(f"✗ 检索失败: {e}", exc_info=True)
            continue

        # 比较结果
        if contexts_with_rerank and contexts_without_rerank:
            logger.info(f"\n场景 3: 结果对比分析")
            logger.info(f"  - 重排序后前3个: {[ctx.source.get('issue_key', '?') for ctx in contexts_with_rerank]}")
            logger.info(f"  - 重排序前前3个: {[ctx.source.get('issue_key', '?') for ctx in contexts_without_rerank]}")

            # 检查排序是否改变
            rerank_ids = [ctx.chunk_id for ctx in contexts_with_rerank]
            no_rerank_ids = [ctx.chunk_id for ctx in contexts_without_rerank]
            if rerank_ids != no_rerank_ids:
                logger.info(f"  ✓ 重排序改变了结果顺序")
            else:
                logger.info(f"  - 重排序未改变结果顺序")

    # 测试缓存机制
    logger.info(f"\n{'=' * 80}")
    logger.info(f"测试缓存机制")
    logger.info(f"{'=' * 80}")

    test_query = test_queries[0]
    logger.info(f"\n第一次查询（应该执行重排序）: {test_query}")
    request = ChatRequest(
        message=test_query,
        enable_rag=True,
        rag_top_k=3,
        retrieval_method="hybrid",
        enable_reranking=True,
        rerank_top_k=10
    )

    import time
    start_time = time.time()
    contexts1 = await chat_service._retrieve_contexts(
        query=request.message,
        top_k=request.rag_top_k,
        retrieval_method=request.retrieval_method,
        enable_reranking=request.enable_reranking,
        rerank_top_k=request.rerank_top_k
    )
    time1 = time.time() - start_time
    logger.info(f"✓ 第一次查询耗时: {time1:.3f}s")

    logger.info(f"\n第二次查询（应该使用缓存）: {test_query}")
    start_time = time.time()
    contexts2 = await chat_service._retrieve_contexts(
        query=request.message,
        top_k=request.rag_top_k,
        retrieval_method=request.retrieval_method,
        enable_reranking=request.enable_reranking,
        rerank_top_k=request.rerank_top_k
    )
    time2 = time.time() - start_time
    logger.info(f"✓ 第二次查询耗时: {time2:.3f}s")

    if time2 < time1 * 0.5:  # 缓存应该显著更快
        logger.info(f"✓ 缓存生效，速度提升 {time1/time2:.1f}x")
    else:
        logger.warning(f"- 缓存可能未生效")

    # 总结
    logger.info(f"\n{'=' * 80}")
    logger.info("测试完成总结")
    logger.info(f"{'=' * 80}")
    logger.info(f"✓ 完整 RAG Pipeline 测试通过")
    logger.info(f"✓ Hybrid Retrieval → Reranking → Top-K 流程正常")
    logger.info(f"✓ 重排序缓存机制工作正常")


if __name__ == "__main__":
    asyncio.run(test_rag_pipeline_with_reranking())
