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
from .routes import chat_router, health_router, models_router
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

    # 预加载模型
    logger.info("Preloading models...")
    try:
        llm_manager = get_llm_manager()
        llm_manager.create_llm()  # 预加载默认 LLM
        llm_manager.create_embedding()  # 预加载默认 Embedding
        logger.info("Models preloaded successfully")
    except Exception as e:
        logger.error(f"Failed to preload models: {e}", exc_info=True)

    yield

    # 关闭时
    logger.info("Shutting down FastAPI application...")
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
