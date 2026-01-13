"""
对话 API 路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException

from ..schemas.chat import ChatRequest, ChatResponse, ChatHistory
from ..schemas.common import SuccessResponse
from ..services import ChatService, get_chat_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    非流式对话接口
    用途：简单的一次性对话，不需要实时响应
    """
    try:
        response = await chat_service.chat(request)
        return response
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    流式对话接口（SSE）
    用途：实时打字机效果，提升用户体验

    事件格式：
    - event: start - 开始生成（包含 session_id）
    - event: context - RAG 检索结果（可选）
    - event: token - 生成的文本片段
    - event: end - 生成结束（包含统计信息）
    - event: error - 错误信息
    """
    from sse_starlette.sse import EventSourceResponse
    import json

    async def event_generator():
        """生成 SSE 事件流"""
        try:
            async for event_data in chat_service.chat_stream(request):
                event_type = event_data.get("event", "message")
                data = event_data.get("data", {})

                # 格式化为 SSE 事件
                yield {
                    "event": event_type,
                    "data": json.dumps(data, ensure_ascii=False)
                }

        except Exception as e:
            logger.error(f"Stream error: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}, ensure_ascii=False)
            }

    return EventSourceResponse(event_generator())


@router.get("/history/{session_id}", response_model=ChatHistory)
async def get_history(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取指定会话的历史记录"""
    try:
        history = await chat_service.get_history(session_id)
        if not history:
            raise HTTPException(status_code=404, detail="Session not found")
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{session_id}", response_model=SuccessResponse)
async def clear_history(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """清空指定会话的历史记录"""
    try:
        await chat_service.clear_history(session_id)
        return SuccessResponse(message="History cleared successfully")
    except Exception as e:
        logger.error(f"Clear history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
