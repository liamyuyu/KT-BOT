"""
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.core.llm.manager import get_llm_manager
from .routes import chat_router, health_router, models_router, sync_router
from .routes.documents import router as documents_router

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
