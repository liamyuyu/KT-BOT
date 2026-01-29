"""
文档管理 API 路由
"""
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Query
from typing import List, Optional
from sse_starlette.sse import EventSourceResponse

from ..schemas.document import (
    DocumentUploadRequest, DocumentUpdateRequest, DocumentQueryRequest,
    DocumentMetadata, DocumentDetail, DocumentListResponse,
    DocumentUploadResponse, DocumentDeleteResponse, DocumentStatsResponse
)
from ..schemas.upload import (
    BatchUploadResponse, UploadTaskResponse, TaskCancelResponse,
    FileRejection
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


@router.post("/upload-file", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form("")
):
    """
    上传文档文件（PDF、Word、Markdown）

    Args:
        file: 上传的文件
        title: 文档标题（可选，留空则自动提取）
        tags: 标签（逗号分隔）

    Returns:
        上传响应

    Raises:
        HTTPException: 上传失败
    """
    # 验证文件类型
    allowed_extensions = ['.pdf', '.docx', '.doc', '.md']
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. Supported types: {', '.join(allowed_extensions)}"
        )

    # 验证文件大小（最大 10MB）
    content = await file.read()
    max_size = 10 * 1024 * 1024  # 10MB
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large: {len(content)} bytes (max: {max_size} bytes)"
        )

    # 保存到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 解析文档
        from src.document_processing.parser.factory import get_parser_factory
        factory = get_parser_factory()
        parsed = await factory.parse_file(tmp_path)

        # 上传到文档服务
        service = get_document_service()
        tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

        request = DocumentUploadRequest(
            title=title or parsed.title,
            content=parsed.content,
            source_type="local_file",
            source_id=f"file_{Path(file.filename).stem}",
            tags=tags_list,
            metadata={
                **parsed.metadata,
                "file_type": parsed.file_type,
                "word_count": parsed.word_count,
                "original_filename": file.filename
            }
        )

        response = await service.upload_document(request)
        return response

    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Parser dependency missing: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse or upload file: {str(e)}"
        )
    finally:
        # 清理临时文件
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass


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


# ========== 批量上传端点 (Story 5.2) ==========

@router.post("/batch-upload", response_model=BatchUploadResponse, status_code=status.HTTP_201_CREATED)
async def batch_upload_documents(
    files: List[UploadFile] = File(...),
    user_id: str = Query(..., description="用户 ID"),
    tags: Optional[str] = Form(None, description="标签（逗号分隔）")
):
    """
    批量上传文档

    限制:
    - 最多 10 个文件
    - 单文件最大 50MB
    - 支持格式: PDF, DOCX, MD, HTML

    Args:
        files: 上传的文件列表
        user_id: 用户 ID
        tags: 标签（逗号分隔）

    Returns:
        BatchUploadResponse: 批量上传响应

    Raises:
        HTTPException: 上传失败
    """
    if len(files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="批量上传最多支持 10 个文件"
        )

    # 解析标签
    tags_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    try:
        from src.services.upload import get_upload_manager
        manager = get_upload_manager()
        response = await manager.submit_batch(files, user_id, tags_list)

        # 转换为 API 响应格式
        return BatchUploadResponse(
            batch_id=response.batch_id,
            total_files=response.total_files,
            accepted_files=response.accepted_files,
            rejected_files=[
                FileRejection(file_name=r["file_name"], reason=r["reason"])
                for r in response.rejected_files
            ],
            task_ids=response.task_ids
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量上传失败: {str(e)}"
        )


@router.get("/upload/{task_id}/progress")
async def get_upload_progress(task_id: str):
    """
    获取上传进度（SSE 流）

    事件格式:
    - event: progress
    - data: {"task_id": "...", "status": "parsing", "progress": 30, ...}

    Args:
        task_id: 任务 ID

    Returns:
        EventSourceResponse: SSE 事件流

    Raises:
        HTTPException: 任务不存在
    """
    try:
        from src.services.upload import get_upload_manager, TaskNotFoundException
        manager = get_upload_manager()

        async def event_generator():
            """生成 SSE 事件"""
            try:
                async for progress in manager.get_progress_stream(task_id):
                    yield {
                        "event": "progress",
                        "data": progress.model_dump_json()
                    }
            except Exception as e:
                # 发送错误事件
                yield {
                    "event": "error",
                    "data": f'{{"error": "{str(e)}"}}'
                }

        return EventSourceResponse(event_generator())

    except TaskNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取进度失败: {str(e)}"
        )


@router.get("/upload/tasks", response_model=List[UploadTaskResponse])
async def list_upload_tasks(
    user_id: str = Query(..., description="用户 ID"),
    status: Optional[str] = Query(None, description="状态筛选"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制")
):
    """
    获取上传任务列表

    Args:
        user_id: 用户 ID
        status: 状态筛选（可选）
        limit: 返回数量限制

    Returns:
        List[UploadTaskResponse]: 任务列表
    """
    try:
        from src.services.upload import get_upload_manager
        manager = get_upload_manager()
        tasks = await manager.list_tasks(user_id, status, limit)

        # 转换为 API 响应格式
        return [
            UploadTaskResponse(
                task_id=task.task_id,
                batch_id=task.batch_id,
                file_name=task.file_info.file_name,
                file_size=task.file_info.file_size,
                status=task.status.value,
                progress_percentage=task.progress_percentage,
                document_id=task.document_id,
                error_message=task.error_message,
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at
            )
            for task in tasks
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.post("/upload/{task_id}/cancel", response_model=TaskCancelResponse)
async def cancel_upload(task_id: str):
    """
    取消上传任务

    Args:
        task_id: 任务 ID

    Returns:
        TaskCancelResponse: 取消响应

    Raises:
        HTTPException: 任务不存在或已完成
    """
    try:
        from src.services.upload import get_upload_manager, TaskNotFoundException
        manager = get_upload_manager()
        success = await manager.cancel_task(task_id)

        if not success:
            return TaskCancelResponse(
                task_id=task_id,
                message="任务已完成或失败，无法取消",
                success=False
            )

        return TaskCancelResponse(
            task_id=task_id,
            message="任务已标记为取消",
            success=True
        )

    except TaskNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消任务失败: {str(e)}"
        )
