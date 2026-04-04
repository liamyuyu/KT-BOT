"""
对话历史 API 路由
Story 5.1 Phase 3
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.database import get_db
from src.services.conversation import (
    ConversationManager,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetail,
    ConversationListResponse,
    ConversationStats,
    MessageCreate,
    MessageResponse,
    ExportFormat,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/conversations", tags=["conversations"])


# ========================================================================
# 依赖注入
# ========================================================================

def get_conversation_manager(
    db: AsyncSession = Depends(get_db)
) -> ConversationManager:
    """获取对话管理器实例"""
    return ConversationManager(session=db)


def get_user_id(
    x_user_id: str = Query(..., alias="user_id", description="用户 ID")
) -> str:
    """
    从查询参数获取用户 ID

    注: MVP 阶段使用查询参数传递用户 ID，
    生产环境应从认证 token 中提取
    """
    if not x_user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    return x_user_id


# ========================================================================
# 对话 CRUD
# ========================================================================

@router.post("", response_model=Dict[str, Any], status_code=201)
async def create_conversation(
    request: ConversationCreate,
    user_id: str = Depends(get_user_id),
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    创建新对话

    Args:
        request: 对话创建请求
        user_id: 用户 ID
        manager: 对话管理器

    Returns:
        创建的对话信息
    """
    try:
        logger.info(f"Creating conversation: user_id={user_id}, title={request.title}")

        conversation = await manager.create_conversation(
            user_id=user_id,
            request=request
        )

        return {
            "data": conversation.model_dump(),
            "message": "Conversation created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("", response_model=Dict[str, Any])
async def list_conversations(
    user_id: str = Depends(get_user_id),
    page: int = Query(1, ge=1, description="页码（从1开始）"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    include_deleted: bool = Query(False, description="是否包含已删除的对话"),
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    获取对话列表（分页）

    Args:
        user_id: 用户 ID
        page: 页码
        page_size: 每页数量
        include_deleted: 是否包含已删除
        manager: 对话管理器

    Returns:
        对话列表
    """
    try:
        logger.info(
            f"Listing conversations: user_id={user_id}, page={page}, "
            f"page_size={page_size}"
        )

        response = await manager.list_conversations(
            user_id=user_id,
            page=page,
            page_size=page_size,
            include_deleted=include_deleted
        )

        return {
            "data": response.model_dump(),
            "message": f"Found {response.total} conversations"
        }

    except Exception as e:
        logger.error(f"Failed to list conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/search", response_model=Dict[str, Any])
async def search_conversations(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    user_id: str = Depends(get_user_id),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    搜索对话（按标题搜索）

    Args:
        keyword: 搜索关键词
        user_id: 用户 ID
        page: 页码
        page_size: 每页数量
        manager: 对话管理器

    Returns:
        搜索结果
    """
    try:
        logger.info(
            f"Searching conversations: user_id={user_id}, keyword='{keyword}', "
            f"page={page}"
        )

        response = await manager.search_conversations(
            user_id=user_id,
            keyword=keyword,
            page=page,
            page_size=page_size
        )

        return {
            "data": response.model_dump(),
            "message": f"Found {response.total} matching conversations"
        }

    except Exception as e:
        logger.error(f"Failed to search conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search conversations: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_conversation_stats(
    user_id: str = Depends(get_user_id),
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    获取对话统计信息

    Args:
        user_id: 用户 ID
        manager: 对话管理器

    Returns:
        统计信息
    """
    try:
        logger.info(f"Getting conversation stats: user_id={user_id}")

        stats = await manager.get_stats(user_id=user_id)

        return {
            "data": stats.model_dump(),
            "message": "Stats retrieved successfully"
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(
    conversation_id: str = Path(..., description="对话 ID"),
    include_messages: bool = Query(True, description="是否包含消息列表"),
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    获取对话详情

    Args:
        conversation_id: 对话 ID
        include_messages: 是否包含消息列表
        manager: 对话管理器

    Returns:
        对话详情
    """
    try:
        logger.info(
            f"Getting conversation: id={conversation_id}, "
            f"include_messages={include_messages}"
        )

        conversation = await manager.get_conversation(
            conversation_id=conversation_id,
            include_messages=include_messages
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "data": conversation.model_dump(),
            "message": "Conversation retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.put("/{conversation_id}", response_model=Dict[str, Any])
async def update_conversation(
    conversation_id: str = Path(..., description="对话 ID"),
    request: ConversationUpdate = ...,
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    更新对话

    Args:
        conversation_id: 对话 ID
        request: 更新请求
        manager: 对话管理器

    Returns:
        更新后的对话
    """
    try:
        logger.info(f"Updating conversation: id={conversation_id}")

        conversation = await manager.update_conversation(
            conversation_id=conversation_id,
            request=request
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "data": conversation.model_dump(),
            "message": "Conversation updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update conversation: {str(e)}")


@router.delete("/{conversation_id}", response_model=Dict[str, Any])
async def delete_conversation(
    conversation_id: str = Path(..., description="对话 ID"),
    soft_delete: bool = Query(True, description="是否软删除"),
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    删除对话

    Args:
        conversation_id: 对话 ID
        soft_delete: 是否软删除（默认 True）
        manager: 对话管理器

    Returns:
        删除结果
    """
    try:
        logger.info(
            f"Deleting conversation: id={conversation_id}, "
            f"soft_delete={soft_delete}"
        )

        success = await manager.delete_conversation(
            conversation_id=conversation_id,
            soft_delete=soft_delete
        )

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "data": {"conversation_id": conversation_id},
            "message": "Conversation deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


@router.post("/batch-delete", response_model=Dict[str, Any])
async def delete_conversations_batch(
    conversation_ids: List[str] = Query(..., description="对话 ID 列表"),
    soft_delete: bool = Query(True, description="是否软删除"),
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    批量删除对话

    Args:
        conversation_ids: 对话 ID 列表
        soft_delete: 是否软删除
        manager: 对话管理器

    Returns:
        删除结果
    """
    try:
        logger.info(
            f"Batch deleting conversations: count={len(conversation_ids)}, "
            f"soft_delete={soft_delete}"
        )

        deleted_count = await manager.delete_conversations_batch(
            conversation_ids=conversation_ids,
            soft_delete=soft_delete
        )

        return {
            "data": {
                "requested": len(conversation_ids),
                "deleted": deleted_count
            },
            "message": f"Deleted {deleted_count} conversations"
        }

    except Exception as e:
        logger.error(f"Failed to batch delete conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to batch delete: {str(e)}")


# ========================================================================
# 消息管理
# ========================================================================

@router.post("/{conversation_id}/messages", response_model=Dict[str, Any], status_code=201)
async def add_message(
    conversation_id: str = Path(..., description="对话 ID"),
    request: MessageCreate = ...,
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    添加消息到对话

    Args:
        conversation_id: 对话 ID
        request: 消息创建请求
        manager: 对话管理器

    Returns:
        创建的消息
    """
    try:
        logger.info(
            f"Adding message: conversation_id={conversation_id}, "
            f"role={request.role}"
        )

        message = await manager.add_message(
            conversation_id=conversation_id,
            request=request
        )

        if not message:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "data": message.model_dump(),
            "message": "Message added successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.get("/{conversation_id}/messages", response_model=Dict[str, Any])
async def get_messages(
    conversation_id: str = Path(..., description="对话 ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    获取对话的消息列表

    Args:
        conversation_id: 对话 ID
        page: 页码
        page_size: 每页数量
        manager: 对话管理器

    Returns:
        消息列表
    """
    try:
        logger.info(
            f"Getting messages: conversation_id={conversation_id}, "
            f"page={page}, page_size={page_size}"
        )

        messages = await manager.get_messages(
            conversation_id=conversation_id,
            page=page,
            page_size=page_size
        )

        return {
            "data": {
                "messages": [msg.model_dump() for msg in messages],
                "count": len(messages),
                "page": page,
                "page_size": page_size
            },
            "message": f"Retrieved {len(messages)} messages"
        }

    except Exception as e:
        logger.error(f"Failed to get messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.delete("/messages/{message_id}", response_model=Dict[str, Any])
async def delete_message(
    message_id: str = Path(..., description="消息 ID"),
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Dict[str, Any]:
    """
    删除消息

    Args:
        message_id: 消息 ID
        manager: 对话管理器

    Returns:
        删除结果
    """
    try:
        logger.info(f"Deleting message: id={message_id}")

        success = await manager.delete_message(message_id=message_id)

        if not success:
            raise HTTPException(status_code=404, detail="Message not found")

        return {
            "data": {"message_id": message_id},
            "message": "Message deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")


# ========================================================================
# 对话导出
# ========================================================================

@router.get("/{conversation_id}/export", response_class=Response)
async def export_conversation(
    conversation_id: str = Path(..., description="对话 ID"),
    format: ExportFormat = Query(ExportFormat.MARKDOWN, description="导出格式"),
    include_metadata: bool = Query(True, description="是否包含元数据"),
    include_contexts: bool = Query(False, description="是否包含RAG上下文"),
    manager: ConversationManager = Depends(get_conversation_manager)
) -> Response:
    """
    导出对话

    支持格式：
    - markdown: Markdown 文件
    - json: JSON 文件
    - pdf: PDF 文件

    Args:
        conversation_id: 对话 ID
        format: 导出格式
        include_metadata: 是否包含元数据
        include_contexts: 是否包含RAG上下文
        manager: 对话管理器

    Returns:
        导出的文件内容
    """
    try:
        logger.info(
            f"Exporting conversation: id={conversation_id}, format={format.value}"
        )

        content = await manager.export_conversation(
            conversation_id=conversation_id,
            format=format,
            include_metadata=include_metadata,
            include_contexts=include_contexts
        )

        if not content:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # 设置响应头
        media_types = {
            ExportFormat.MARKDOWN: "text/markdown",
            ExportFormat.JSON: "application/json",
            ExportFormat.PDF: "application/pdf"
        }

        extensions = {
            ExportFormat.MARKDOWN: "md",
            ExportFormat.JSON: "json",
            ExportFormat.PDF: "pdf"
        }

        media_type = media_types.get(format, "application/octet-stream")
        extension = extensions.get(format, "txt")
        filename = f"conversation_{conversation_id}.{extension}"

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export conversation: {str(e)}")
