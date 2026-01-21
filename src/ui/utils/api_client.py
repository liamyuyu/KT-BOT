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
        rerank_top_k: int = 10
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
            "rerank_top_k": rerank_top_k
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
        rerank_top_k: int = 10
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
            "rerank_top_k": rerank_top_k
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

    async def get_models(self) -> List[str]:
        """获取可用模型列表"""
        url = f"{self.base_url}{self.api_prefix}/models/list"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("data", {}).get("models", [])

        except Exception as e:
            logger.error(f"Get models failed: {e}")
            # 返回默认模型列表
            return ["qwen2.5:7b", "qwen2.5:14b", "llama3.1:8b"]

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


# 全局客户端实例
_client: Optional[ChatAPIClient] = None


def get_api_client() -> ChatAPIClient:
    """获取 API 客户端单例"""
    global _client
    if _client is None:
        _client = ChatAPIClient()
    return _client
