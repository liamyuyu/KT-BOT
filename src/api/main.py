"""
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.config import settings
from src.core.llm.manager import get_llm_manager
from .routes import (
    chat_router,
    health_router,
    models_router,
    sync_router,
    conversations_router,
    citations_router
)
from .routes.documents import router as documents_router
from .routes.search import router as search_router
from .routes.metrics import router as metrics_router
from .middleware.timing import TimingMiddleware, set_timing_middleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    # 启动时
    logger.info("Starting FastAPI application...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

    # 启动同步调度器
    logger.info("Starting sync scheduler...")
    try:
        from src.services.sync import get_sync_scheduler
        scheduler = get_sync_scheduler()
        await scheduler.start()
        logger.info("✅ Sync scheduler started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start sync scheduler: {e}", exc_info=True)
        # 调度器启动失败不应该阻止应用启动
        if settings.environment == "production":
            logger.warning("⚠️  Sync scheduler failed to start in production mode")

    # 加载配置
    llm_manager = get_llm_manager()
    config = llm_manager.config

    # 启动时健康检查
    if config.health_check.enabled and config.health_check.startup_check:
        logger.info("Performing startup health check...")
        from src.core.llm.health import get_health_checker

        checker = get_health_checker()
        health_results = await checker.check_all()
        overall = checker.get_overall_status(health_results)

        if overall == "unhealthy":
            logger.error("⚠️  Startup health check failed!")
            for name, status in health_results.items():
                if status.status == "unhealthy":
                    logger.error(f"  ❌ {name}: {status.error}")

            # 根据配置决定是否阻止启动
            if settings.environment == "production":
                raise RuntimeError("Model health check failed at startup")
            else:
                logger.warning("⚠️  Continuing in development mode...")
        else:
            logger.info("✅ All models healthy")

    # 预加载模型
    logger.info("Preloading models...")
    try:
        llm_manager.create_llm()  # 预加载默认 LLM
        llm_manager.create_embedding()  # 预加载默认 Embedding
        logger.info("✅ Models preloaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to preload models: {e}", exc_info=True)
        if settings.environment == "production":
            raise

    # 初始化 BM25 索引（如果存在）
    logger.info("Loading BM25 index...")
    try:
        from src.core.rag.retriever.bm25 import get_bm25_retriever
        from pathlib import Path

        bm25_retriever = get_bm25_retriever()
        bm25_cache_file = Path(bm25_retriever.bm25_config.cache_dir) / "bm25_index.pkl"

        if bm25_cache_file.exists():
            bm25_retriever.load_index()
            stats = bm25_retriever.get_statistics()
            logger.info(f"✅ BM25 index loaded: {stats.get('document_count', 0)} documents")
        else:
            logger.warning(
                "⚠️  BM25 index not found. Run 'python scripts/init_bm25.py' to initialize it. "
                "Hybrid retrieval will fall back to vector-only mode."
            )
    except Exception as e:
        logger.warning(f"⚠️  Failed to load BM25 index: {e}. Continuing without BM25.")

    yield

    # 关闭时
    logger.info("Shutting down FastAPI application...")

    # 关闭同步调度器
    try:
        from src.services.sync import get_sync_scheduler
        scheduler = get_sync_scheduler()
        if scheduler.is_running():
            await scheduler.shutdown(wait=True)
            logger.info("Sync scheduler shut down")
    except Exception as e:
        logger.error(f"Error shutting down sync scheduler: {e}", exc_info=True)

    # 关闭 LLM 管理器
    try:
        llm_manager = get_llm_manager()
        await llm_manager.close_all()
        logger.info("All models closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


def create_fastapi_app() -> FastAPI:
    """
    创建 FastAPI 应用
    """
    app = FastAPI(
        title="KT-BOT API",
        description="Enterprise Knowledge Bot API",
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # 性能监控中间件（在所有路由之前添加）
    # The middleware uses class-level storage, so all instances share the same records
    app.add_middleware(TimingMiddleware, max_records=1000)

    # Create a reference instance for the metrics routes to access
    # Since records are shared at class level, this instance will see all recorded requests
    _timing_instance = TimingMiddleware(app, max_records=1000)
    set_timing_middleware(_timing_instance)

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # MVP 阶段允许所有来源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")
    app.include_router(models_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(sync_router, prefix="/api/v1")
    app.include_router(search_router, prefix="/api/v1")
    app.include_router(conversations_router, prefix="/api/v1")
    app.include_router(citations_router, prefix="/api/v1")
    app.include_router(metrics_router, prefix="/api/v1/metrics", tags=["监控"])

    # 验证错误处理
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc: RequestValidationError):
        logger.error(f"=== Validation Error ===")
        logger.error(f"URL: {request.url}")
        logger.error(f"Method: {request.method}")

        try:
            body = await request.body()
            logger.error(f"Request Body: {body.decode('utf-8')}")
        except:
            pass

        logger.error(f"Validation Errors:")
        for error in exc.errors():
            logger.error(f"  - Field: {error['loc']}")
            logger.error(f"    Error: {error['msg']}")
            logger.error(f"    Type: {error['type']}")

        logger.error(f"========================")

        return JSONResponse(
            status_code=422,
            content={
                "detail": exc.errors()
            }
        )

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "InternalServerError",
                "message": str(exc) if settings.debug else "Internal server error"
            }
        )

    logger.info("FastAPI application created")
    return app


# 创建应用实例
app = create_fastapi_app()
