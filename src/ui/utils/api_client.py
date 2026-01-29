"""
FastAPI 客户端 - Gradio 前端调用后端 API
"""
import logging
from typing import Optional, List, Dict, Any, AsyncIterator
import httpx
import json

logger = logging.getLogger(__name__)


class ChatAPIClient:
    """对话 API 客户端"""

    def __init__(self, base_url: str = "http://localhost:7860"):
        """
        初始化 API 客户端

        Args:
            base_url: FastAPI 服务器地址
        """
        self.base_url = base_url.rstrip("/")
        self.api_prefix = "/api/v1"
        self.timeout = 60.0

        logger.info(f"ChatAPIClient initialized with base_url: {self.base_url}")

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}{self.api_prefix}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        model_name: Optional[str] = None,
        enable_rag: bool = True,
        rag_top_k: int = 3,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        retrieval_method: str = "hybrid",
        fusion_method: str = "rrf",
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        enable_reranking: bool = True,
        rerank_top_k: int = 10,
        filter_sources: Optional[List[str]] = None,
        filter_time_preset: Optional[str] = None,
        filter_doc_types: Optional[List[str]] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        非流式对话

        Args:
            message: 用户消息
            session_id: 会话 ID
            model_name: 模型名称
            enable_rag: 是否启用 RAG
            rag_top_k: RAG 检索数量
            temperature: 生成温度
            max_tokens: 最大 token 数
            retrieval_method: 检索方法（vector/bm25/hybrid）
            fusion_method: 融合方法（rrf/weighted/linear）
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重
            enable_reranking: 是否启用重排序
            rerank_top_k: 重排序候选数量
            filter_sources: 过滤来源（jira/confluence/local）
            filter_time_preset: 时间范围预设（1d/7d/30d/90d）
            filter_doc_types: 文档类型过滤
            filter_metadata: 元数据过滤

        Returns:
            响应数据字典
        """
        url = f"{self.base_url}{self.api_prefix}/chat/message"

        request_data = {
            "message": message,
            "session_id": session_id,
            "model_name": model_name,
            "enable_rag": enable_rag,
            "rag_top_k": rag_top_k,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "retrieval_method": retrieval_method,
            "fusion_method": fusion_method,
            "vector_weight": vector_weight,
            "bm25_weight": bm25_weight,
            "enable_reranking": enable_reranking,
            "rerank_top_k": rerank_top_k,
            "filter_sources": filter_sources,
            "filter_time_preset": filter_time_preset,
            "filter_doc_types": filter_doc_types,
            "filter_metadata": filter_metadata
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=request_data)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"API 错误: {e.response.status_code}")
        except httpx.ConnectError:
            logger.error("Failed to connect to FastAPI server")
            raise Exception("无法连接到后端服务，请确保 FastAPI 服务器正在运行")
        except Exception as e:
            logger.error(f"Chat request failed: {e}")
            raise

    async def chat_stream(
        self,
        message: str,
        session_id: Optional[str] = None,
        model_name: Optional[str] = None,
        enable_rag: bool = True,
        rag_top_k: int = 3,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        retrieval_method: str = "hybrid",
        fusion_method: str = "rrf",
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        enable_reranking: bool = True,
        rerank_top_k: int = 10,
        filter_sources: Optional[List[str]] = None,
        filter_time_preset: Optional[str] = None,
        filter_doc_types: Optional[List[str]] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式对话（SSE）

        Args:
            message: 用户消息
            session_id: 会话 ID
            model_name: 模型名称
            enable_rag: 是否启用 RAG
            rag_top_k: RAG 检索数量
            temperature: 生成温度
            max_tokens: 最大 token 数
            retrieval_method: 检索方法（vector/bm25/hybrid）
            fusion_method: 融合方法（rrf/weighted/linear）
            vector_weight: 向量检索权重
            bm25_weight: BM25 检索权重
            enable_reranking: 是否启用重排序
            rerank_top_k: 重排序候选数量
            filter_sources: 过滤来源（jira/confluence/local）
            filter_time_preset: 时间范围预设（1d/7d/30d/90d）
            filter_doc_types: 文档类型过滤
            filter_metadata: 元数据过滤

        Yields:
            事件字典 {"event": "...", "data": {...}}
        """
        url = f"{self.base_url}{self.api_prefix}/chat/stream"

        request_data = {
            "message": message,
            "session_id": session_id,
            "model_name": model_name,
            "enable_rag": enable_rag,
            "rag_top_k": rag_top_k,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "retrieval_method": retrieval_method,
            "fusion_method": fusion_method,
            "vector_weight": vector_weight,
            "bm25_weight": bm25_weight,
            "enable_reranking": enable_reranking,
            "rerank_top_k": rerank_top_k,
            "filter_sources": filter_sources,
            "filter_time_preset": filter_time_preset,
            "filter_doc_types": filter_doc_types,
            "filter_metadata": filter_metadata
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    json=request_data,
                    headers={"Accept": "text/event-stream"}
                ) as response:
                    response.raise_for_status()

                    event_type = None
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        # 解析 SSE 事件
                        if line.startswith("event:"):
                            event_type = line[6:].strip()

                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                            try:
                                data = json.loads(data_str)
                                yield {
                                    "event": event_type or "message",
                                    "data": data
                                }
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse SSE data: {data_str[:100]}")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code}")
            yield {
                "event": "error",
                "data": {"message": f"API 错误: {e.response.status_code}"}
            }
        except httpx.ConnectError:
            logger.error("Failed to connect to FastAPI server")
            yield {
                "event": "error",
                "data": {"message": "无法连接到后端服务"}
            }
        except Exception as e:
            logger.error(f"Stream request failed: {e}")
            yield {
                "event": "error",
                "data": {"message": str(e)}
            }

    async def get_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取历史记录"""
        url = f"{self.base_url}{self.api_prefix}/chat/history/{session_id}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)

                if response.status_code == 404:
                    return None

                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get history failed: {e}")
            return None

    async def clear_history(self, session_id: str) -> bool:
        """清空历史记录"""
        url = f"{self.base_url}{self.api_prefix}/chat/history/{session_id}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(url)
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Clear history failed: {e}")
            return False

    async def get_models(self) -> Dict[str, Any]:
        """
        获取可用模型列表和当前模型

        Returns:
            {
                "models": {"llm": [...], "embedding": [...]},
                "current": {"llm": "...", "embedding": "..."}
            }
        """
        url = f"{self.base_url}{self.api_prefix}/models/list"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("data", {
                    "models": {
                        "llm": ["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b"],
                        "embedding": ["nomic-embed-text", "mxbai-embed-large"]
                    },
                    "current": {"llm": None, "embedding": None}
                })

        except Exception as e:
            logger.error(f"Get models failed: {e}")
            # 返回默认模型列表
            return {
                "models": {
                    "llm": ["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b"],
                    "embedding": ["nomic-embed-text", "mxbai-embed-large"]
                },
                "current": {"llm": None, "embedding": None}
            }

    async def get_model_status(self) -> Optional[Dict[str, Any]]:
        """
        获取模型状态（包括健康检查）

        Returns:
            {
                "current_models": {"llm": "...", "embedding": "..."},
                "health": {"llm": true, "embedding": true}
            }
        """
        url = f"{self.base_url}{self.api_prefix}/models/status"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("data")

        except Exception as e:
            logger.error(f"Get model status failed: {e}")
            return None

    async def switch_llm_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        切换 LLM 对话模型

        Args:
            model_name: 目标模型名称

        Returns:
            切换结果
        """
        url = f"{self.base_url}{self.api_prefix}/models/switch-llm"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json={"model_name": model_name})
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Switch LLM model failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Switch LLM model failed: {e}")
            return None

    async def switch_embedding_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        切换 Embedding 模型

        Args:
            model_name: 目标模型名称

        Returns:
            切换结果（包含警告信息）
        """
        url = f"{self.base_url}{self.api_prefix}/models/switch-embedding"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json={"model_name": model_name})
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Switch embedding model failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Switch embedding model failed: {e}")
            return None

    # ============ 文档管理 API ============

    async def upload_document(
        self,
        title: str,
        content: str,
        source_type: str = "local",
        source_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        上传文档

        Args:
            title: 文档标题
            content: 文档内容
            source_type: 来源类型
            source_id: 来源ID
            tags: 标签列表
            metadata: 额外元数据

        Returns:
            上传响应数据
        """
        url = f"{self.base_url}{self.api_prefix}/documents/upload"

        request_data = {
            "title": title,
            "content": content,
            "source_type": source_type,
            "source_id": source_id,
            "tags": tags or [],
            "metadata": metadata or {}
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=request_data)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Upload document failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Upload document failed: {e}")
            return None

    async def upload_document_file(
        self,
        file_path: str,
        title: Optional[str] = None,
        tags: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        上传文档文件（PDF、Word、Markdown）

        Args:
            file_path: 文件路径
            title: 文档标题（可选，留空则自动提取）
            tags: 标签（逗号分隔字符串）

        Returns:
            上传响应数据
        """
        url = f"{self.base_url}{self.api_prefix}/documents/upload-file"

        try:
            # 打开文件
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.split('/')[-1], f, 'application/octet-stream')}

                # 准备表单数据
                data = {}
                if title:
                    data['title'] = title
                if tags:
                    data['tags'] = tags

                # 使用 multipart/form-data 上传
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(url, files=files, data=data)
                    response.raise_for_status()
                    return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Upload file failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Upload file failed: {e}")
            return None

    async def list_documents(
        self,
        source_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        获取文档列表

        Args:
            source_type: 来源类型筛选
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            文档列表响应
        """
        url = f"{self.base_url}{self.api_prefix}/documents/list"

        params = {
            "limit": limit,
            "offset": offset
        }
        if source_type:
            params["source_type"] = source_type

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"List documents failed: {e}")
            return None

    async def delete_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        删除文档

        Args:
            document_id: 文档ID

        Returns:
            删除响应数据
        """
        url = f"{self.base_url}{self.api_prefix}/documents/{document_id}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(url)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Delete document failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Delete document failed: {e}")
            return None

    async def get_document_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取文档统计信息

        Returns:
            统计响应数据
        """
        url = f"{self.base_url}{self.api_prefix}/documents/stats/summary"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get document stats failed: {e}")
            return None

    # ============ 批量上传 API (Story 5.2) ============

    async def batch_upload_documents(
        self,
        file_paths: List[str],
        user_id: str = "default",
        tags: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        批量上传文档

        Args:
            file_paths: 文件路径列表
            user_id: 用户 ID
            tags: 标签（逗号分隔）

        Returns:
            批量上传响应
        """
        url = f"{self.base_url}{self.api_prefix}/documents/batch-upload?user_id={user_id}"

        try:
            # 准备多个文件
            files = []
            for file_path in file_paths:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    file_name = file_path.split('/')[-1]
                    files.append(('files', (file_name, content, 'application/octet-stream')))

            # 准备表单数据
            data = {}
            if tags:
                data['tags'] = tags

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(url, files=files, data=data)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Batch upload failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Batch upload failed: {e}")
            return None

    async def get_upload_progress_stream(
        self,
        task_id: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        获取上传进度流（SSE）

        Args:
            task_id: 任务 ID

        Yields:
            进度事件字典
        """
        url = f"{self.base_url}{self.api_prefix}/documents/upload/{task_id}/progress"

        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream("GET", url, headers={"Accept": "text/event-stream"}) as response:
                    response.raise_for_status()

                    event_type = None
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                        elif line.startswith("data:"):
                            data_str = line[5:].strip()
                            try:
                                data = json.loads(data_str)
                                yield {
                                    "event": event_type or "progress",
                                    "data": data
                                }
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse progress data: {data_str[:100]}")

        except Exception as e:
            logger.error(f"Get upload progress failed: {e}")
            yield {
                "event": "error",
                "data": {"message": str(e)}
            }

    async def list_upload_tasks(
        self,
        user_id: str = "default",
        status: Optional[str] = None,
        limit: int = 50
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取上传任务列表

        Args:
            user_id: 用户 ID
            status: 状态筛选
            limit: 返回数量限制

        Returns:
            任务列表
        """
        url = f"{self.base_url}{self.api_prefix}/documents/upload/tasks"

        params = {
            "user_id": user_id,
            "limit": limit
        }
        if status:
            params["status"] = status

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"List upload tasks failed: {e}")
            return None

    async def cancel_upload_task(
        self,
        task_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        取消上传任务

        Args:
            task_id: 任务 ID

        Returns:
            取消结果
        """
        url = f"{self.base_url}{self.api_prefix}/documents/upload/{task_id}/cancel"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Cancel upload task failed: {e}")
            return None

    # ============ 搜索 API (Story 4.5) ============

    async def search_documents(
        self,
        query: str,
        method: str = "hybrid",
        top_k: int = 10,
        page: int = 1,
        page_size: int = 10,
        sources: Optional[List[str]] = None,
        doc_types: Optional[List[str]] = None,
        time_range: Optional[str] = None,
        enable_highlight: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        搜索文档

        Args:
            query: 搜索查询
            method: 搜索方法（vector/bm25/hybrid）
            top_k: 返回结果数量
            page: 页码
            page_size: 每页大小
            sources: 来源过滤
            doc_types: 文档类型过滤
            time_range: 时间范围过滤
            enable_highlight: 是否启用关键词高亮

        Returns:
            搜索结果
        """
        url = f"{self.base_url}{self.api_prefix}/search/documents"

        request_data = {
            "query": query,
            "method": method,
            "top_k": top_k,
            "page": page,
            "page_size": page_size,
            "sources": sources,
            "doc_types": doc_types,
            "time_range": time_range,
            "enable_highlight": enable_highlight
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=request_data)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Search documents failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Search documents failed: {e}")
            return None

    async def get_search_methods(self) -> Optional[Dict[str, Any]]:
        """
        获取支持的搜索方法列表

        Returns:
            搜索方法列表
        """
        url = f"{self.base_url}{self.api_prefix}/search/methods"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get search methods failed: {e}")
            return {
                "data": {
                    "methods": [
                        {"value": "hybrid", "label": "混合搜索", "description": "结合向量和全文搜索"},
                        {"value": "vector", "label": "向量搜索", "description": "基于语义相似度"},
                        {"value": "bm25", "label": "全文搜索", "description": "基于关键词匹配"}
                    ],
                    "default": "hybrid"
                }
            }

    # ========================================================================
    # 同步管理 API
    # ========================================================================

    async def trigger_sync(
        self,
        source: str,
        sync_type: str = "incremental",
        created_by: str = "ui"
    ) -> Optional[Dict[str, Any]]:
        """
        触发同步任务

        Args:
            source: 数据源 (jira/confluence)
            sync_type: 同步类型 (full/incremental)
            created_by: 创建者

        Returns:
            触发结果
        """
        url = f"{self.base_url}{self.api_prefix}/sync/trigger/{source}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json={
                        "sync_type": sync_type,
                        "created_by": created_by
                    }
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"Trigger sync failed: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Trigger sync failed: {e}")
            return None

    async def get_scheduler_status(self) -> Optional[Dict[str, Any]]:
        """
        获取调度器状态

        Returns:
            调度器状态信息
        """
        url = f"{self.base_url}{self.api_prefix}/sync/scheduler/status"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get scheduler status failed: {e}")
            return None

    async def get_sync_config(self, source: str) -> Optional[Dict[str, Any]]:
        """
        获取同步配置

        Args:
            source: 数据源 (jira/confluence)

        Returns:
            配置信息
        """
        url = f"{self.base_url}{self.api_prefix}/sync/config/{source}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get sync config failed: {e}")
            return None

    async def reload_sync_config(self) -> Optional[Dict[str, Any]]:
        """
        重新加载同步配置

        Returns:
            操作结果
        """
        url = f"{self.base_url}{self.api_prefix}/sync/config/reload"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Reload sync config failed: {e}")
            return None

    async def get_running_tasks(self) -> Optional[Dict[str, Any]]:
        """
        获取运行中的任务

        Returns:
            运行中的任务列表
        """
        url = f"{self.base_url}{self.api_prefix}/sync/status/running"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get running tasks failed: {e}")
            return None

    async def get_sync_history(
        self,
        source: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        获取同步历史记录

        Args:
            source: 数据源过滤
            status: 状态过滤
            page: 页码
            page_size: 每页大小

        Returns:
            历史记录列表
        """
        url = f"{self.base_url}{self.api_prefix}/sync/history"

        params = {
            "page": page,
            "page_size": page_size
        }
        if source:
            params["source"] = source
        if status:
            params["status"] = status

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get sync history failed: {e}")
            return None

    async def get_sync_statistics(
        self,
        source: Optional[str] = None,
        days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        获取同步统计信息

        Args:
            source: 数据源
            days: 统计最近N天

        Returns:
            统计信息
        """
        url = f"{self.base_url}{self.api_prefix}/sync/statistics"

        params = {"days": days}
        if source:
            params["source"] = source

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get sync statistics failed: {e}")
            return None

    # ============ 对话历史 API (Story 5.1) ============

    async def list_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        获取对话列表

        Args:
            user_id: 用户 ID
            page: 页码
            page_size: 每页数量

        Returns:
            对话列表
        """
        url = f"{self.base_url}{self.api_prefix}/conversations"

        params = {
            "user_id": user_id,
            "page": page,
            "page_size": page_size
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"List conversations failed: {e}")
            return None

    async def search_conversations(
        self,
        user_id: str,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        搜索对话

        Args:
            user_id: 用户 ID
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            搜索结果
        """
        url = f"{self.base_url}{self.api_prefix}/conversations/search"

        params = {
            "user_id": user_id,
            "keyword": keyword,
            "page": page,
            "page_size": page_size
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Search conversations failed: {e}")
            return None

    async def get_conversation(
        self,
        conversation_id: str,
        include_messages: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        获取对话详情

        Args:
            conversation_id: 对话 ID
            include_messages: 是否包含消息

        Returns:
            对话详情
        """
        url = f"{self.base_url}{self.api_prefix}/conversations/{conversation_id}"

        params = {"include_messages": include_messages}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get conversation failed: {e}")
            return None

    async def delete_conversation(
        self,
        conversation_id: str,
        soft_delete: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        删除对话

        Args:
            conversation_id: 对话 ID
            soft_delete: 是否软删除

        Returns:
            删除结果
        """
        url = f"{self.base_url}{self.api_prefix}/conversations/{conversation_id}"

        params = {"soft_delete": soft_delete}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(url, params=params)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Delete conversation failed: {e}")
            return None

    async def get_conversation_stats(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取对话统计

        Args:
            user_id: 用户 ID

        Returns:
            统计信息
        """
        url = f"{self.base_url}{self.api_prefix}/conversations/stats"

        params = {"user_id": user_id}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Get conversation stats failed: {e}")
            return None

    async def export_conversation(
        self,
        conversation_id: str,
        format: str = "markdown"
    ) -> Optional[bytes]:
        """
        导出对话

        Args:
            conversation_id: 对话 ID
            format: 导出格式 (markdown/json/pdf)

        Returns:
            文件内容（字节）
        """
        url = f"{self.base_url}{self.api_prefix}/conversations/{conversation_id}/export"

        params = {"format": format}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.content

        except Exception as e:
            logger.error(f"Export conversation failed: {e}")
            return None


# 全局客户端实例
_client: Optional[ChatAPIClient] = None


def get_api_client() -> ChatAPIClient:
    """获取 API 客户端单例"""
    global _client
    if _client is None:
        _client = ChatAPIClient()
    return _client
