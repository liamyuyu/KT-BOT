"""
文档管理 API 路由
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from ..schemas.document import (
    DocumentUploadRequest, DocumentUpdateRequest, DocumentQueryRequest,
    DocumentMetadata, DocumentDetail, DocumentListResponse,
    DocumentUploadResponse, DocumentDeleteResponse, DocumentStatsResponse
)
from ..services.document_service import get_document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(request: DocumentUploadRequest):
    """
    上传并索引文档

    Args:
        request: 文档上传请求

    Returns:
        上传响应

    Raises:
        HTTPException: 上传失败
    """
    try:
        service = get_document_service()
        response = await service.upload_document(request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/query", response_model=DocumentListResponse)
async def query_documents(request: DocumentQueryRequest):
    """
    查询文档列表

    Args:
        request: 查询请求

    Returns:
        文档列表响应
    """
    service = get_document_service()
    response = await service.get_document_list(request)
    return response


@router.get("/list", response_model=DocumentListResponse)
async def list_documents(
    source_type: str = None,
    limit: int = 100,
    offset: int = 0
):
    """
    获取文档列表（简化接口）

    Args:
        source_type: 来源类型筛选
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        文档列表响应
    """
    query = DocumentQueryRequest(
        source_type=source_type,
        limit=limit,
        offset=offset
    )
    service = get_document_service()
    response = await service.get_document_list(query)
    return response


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(document_id: str):
    """
    获取文档详情

    Args:
        document_id: 文档ID

    Returns:
        文档详情

    Raises:
        HTTPException: 文档不存在
    """
    service = get_document_service()
    document = await service.get_document_by_id(document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    return document


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str):
    """
    删除文档

    Args:
        document_id: 文档ID

    Returns:
        删除响应

    Raises:
        HTTPException: 文档不存在或删除失败
    """
    try:
        service = get_document_service()
        response = await service.delete_document(document_id)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/stats/summary", response_model=DocumentStatsResponse)
async def get_document_stats():
    """
    获取文档统计信息

    Returns:
        统计响应
    """
    service = get_document_service()
    response = await service.get_document_stats()
    return response


@router.put("/{document_id}", response_model=DocumentUploadResponse)
async def update_document(document_id: str, request: DocumentUpdateRequest):
    """
    更新文档（重新索引）

    Args:
        document_id: 文档ID
        request: 更新请求

    Returns:
        上传响应

    Raises:
        HTTPException: 文档不存在或更新失败
    """
    try:
        service = get_document_service()

        # 获取现有文档
        existing = await service.get_document_by_id(document_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        # 准备更新后的内容
        new_title = request.title if request.title else existing.title
        new_content = request.content if request.content else existing.content
        new_tags = request.tags if request.tags is not None else existing.tags
        new_metadata = request.metadata if request.metadata is not None else existing.metadata

        # 删除旧文档
        await service.delete_document(document_id)

        # 重新上传
        upload_request = DocumentUploadRequest(
            title=new_title,
            content=new_content,
            source_type=existing.source_type,
            source_id=existing.source_id,
            tags=new_tags,
            metadata=new_metadata
        )

        response = await service.upload_document(upload_request)
        return response

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
