"""
Gradio UI 应用入口
"""
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import gradio as gr

from src.ui.pages.chat_page import create_chat_page
from src.ui.pages.document_page import create_document_page
from src.config import settings

# 创建日志目录
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(logs_dir / "gradio_ui.log")
    ]
)

logger = logging.getLogger(__name__)


def create_app() -> gr.Blocks:
    """创建 Gradio 应用"""
    logger.info("Creating Gradio application...")

    # 创建各个页面
    chat_page = create_chat_page()
    document_page = create_document_page()

    # 使用 TabbedInterface 组合多个页面
    demo = gr.TabbedInterface(
        [chat_page, document_page],
        ["💬 对话", "📚 文档管理"],
        title="KT-BOT - Enterprise Knowledge Bot"
    )

    logger.info("Gradio application created successfully")
    return demo


def main():
    """启动 Gradio 应用"""
    logger.info("=" * 60)
    logger.info("Starting Gradio UI...")
    logger.info(f"Port: {settings.gradio_port}")
    logger.info(f"Share: {settings.gradio_share}")
    logger.info("=" * 60)

    try:
        # 创建应用
        demo = create_app()

        # 启动服务器
        demo.queue()  # 启用队列支持流式响应
        demo.launch(
            server_name="0.0.0.0",
            server_port=settings.gradio_port,
            share=settings.gradio_share,
            show_error=True,
            show_api=False
        )

    except Exception as e:
        logger.error(f"Failed to start Gradio UI: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
