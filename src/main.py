"""
KT-BOT 主程序入口
并发启动 FastAPI 后端 + Gradio 前端
"""
import logging
import sys
import threading
import time
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn

from src.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/main.log")
    ]
)

logger = logging.getLogger(__name__)


def run_fastapi():
    """启动 FastAPI 后端服务"""
    logger.info("=" * 60)
    logger.info("Starting FastAPI Backend...")
    logger.info(f"Host: 0.0.0.0")
    logger.info(f"Port: 7860")
    logger.info(f"API Docs: http://localhost:7860/docs")
    logger.info("=" * 60)

    try:
        uvicorn.run(
            "src.api.main:app",
            host="0.0.0.0",
            port=7860,
            reload=False,  # 生产模式关闭热重载
            log_level="info"
        )
    except Exception as e:
        logger.error(f"FastAPI failed: {e}", exc_info=True)
        raise


def run_gradio():
    """启动 Gradio 前端服务"""
    logger.info("=" * 60)
    logger.info("Starting Gradio Frontend...")
    logger.info(f"Port: {settings.gradio_port}")
    logger.info(f"UI URL: http://localhost:{settings.gradio_port}")
    logger.info("=" * 60)

    try:
        from src.ui.app import create_app

        # 创建 Gradio 应用
        demo = create_app()

        # 启动服务器
        demo.queue()  # 启用队列支持流式响应
        demo.launch(
            server_name="0.0.0.0",
            server_port=settings.gradio_port,
            share=settings.gradio_share,
            show_error=True,
            show_api=False,
            prevent_thread_lock=False  # 主线程阻塞
        )

    except Exception as e:
        logger.error(f"Gradio failed: {e}", exc_info=True)
        raise


def main():
    """主入口 - 并发启动两个服务"""
    logger.info("=" * 80)
    logger.info("🚀 KT-BOT Starting...")
    logger.info("=" * 80)

    # 检查配置
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Embedding Provider: {settings.embedding_provider}")
    logger.info(f"Vector DB: ChromaDB ({settings.chromadb_path})")

    try:
        # 1. 启动 FastAPI（后台线程）
        logger.info("\n[1/2] Launching FastAPI backend...")
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()

        # 等待 FastAPI 启动
        logger.info("Waiting for FastAPI to be ready...")
        time.sleep(3)

        # 2. 启动 Gradio（主线程，阻塞）
        logger.info("\n[2/2] Launching Gradio frontend...")
        run_gradio()

    except KeyboardInterrupt:
        logger.info("\n" + "=" * 80)
        logger.info("🛑 Shutting down KT-BOT...")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
