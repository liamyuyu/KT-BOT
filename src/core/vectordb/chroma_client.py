"""
ChromaDB Vector Database Client
ChromaDB 向量数据库客户端实现
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.types import QueryResult, GetResult
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from src.config import settings
from src.core.vectordb.models import (
    Document,
    SearchResult,
    SearchResults,
    CollectionInfo,
    HealthStatus,
    BatchInsertResult
)
from src.core.vectordb.exceptions import (
    VectorDBError,
    VectorDBConnectionError,
    VectorDBCollectionError,
    VectorDBQueryError,
    VectorDBInsertError,
    VectorDBNotFoundError
)

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """
    ChromaDB 客户端
    提供向量数据库访问的统一接口

    Features:
    - Collection 管理
    - 文档增删改查
    - 向量相似度搜索
    - 批量操作
    - 健康检查
    - 自动重试和错误处理
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_function: Optional[Any] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        use_persistent: bool = True
    ):
        """
        初始化 ChromaDB 客户端

        Args:
            persist_directory: 持久化目录（默认从配置读取）
            collection_name: 默认 Collection 名称（默认从配置读取）
            embedding_function: Embedding 函数（可选，使用 ChromaDB 默认）
            host: ChromaDB 服务器地址（客户端模式）
            port: ChromaDB 服务器端口（客户端模式）
            use_persistent: 是否使用持久化存储（默认 True）
        """
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name or settings.chroma_collection_name
        self.embedding_function = embedding_function
        self.host = host
        self.port = port
        self.use_persistent = use_persistent

        self._client: Optional[chromadb.ClientAPI] = None
        self._collection: Optional[chromadb.Collection] = None
        self._is_connected = False

    @property
    def client(self) -> chromadb.ClientAPI:
        """获取 ChromaDB 客户端实例（懒加载）"""
        if self._client is None:
            self._connect()
        return self._client

    def _connect(self) -> None:
        """建立 ChromaDB 连接"""
        try:
            logger.info("正在连接 ChromaDB...")

            if self.host and self.port:
                # 客户端模式：连接到远程 ChromaDB 服务器
                logger.info(f"使用客户端模式连接: {self.host}:{self.port}")
                self._client = chromadb.HttpClient(
                    host=self.host,
                    port=self.port
                )
            elif self.use_persistent:
                # 持久化模式：本地存储
                logger.info(f"使用持久化模式，目录: {self.persist_directory}")

                # 确保目录存在
                persist_path = Path(self.persist_directory)
                persist_path.mkdir(parents=True, exist_ok=True)

                self._client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            else:
                # 内存模式：仅用于测试
                logger.warning("使用内存模式（数据不会持久化）")
                self._client = chromadb.EphemeralClient()

            # 测试连接
            self._client.heartbeat()
            self._is_connected = True
            logger.info("ChromaDB 连接成功")

        except Exception as e:
            raise VectorDBConnectionError(f"ChromaDB 连接失败: {str(e)}")

    def get_or_create_collection(
        self,
        collection_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> chromadb.Collection:
        """
        获取或创建 Collection

        Args:
            collection_name: Collection 名称（默认使用配置的名称）
            metadata: Collection 元数据

        Returns:
            Collection 实例
        """
        name = collection_name or self.collection_name

        try:
            collection = self.client.get_or_create_collection(
                name=name,
                metadata=metadata or {"description": "KT-BOT 知识库"},
                embedding_function=self.embedding_function
            )
            logger.info(f"Collection '{name}' 准备就绪")
            return collection
        except Exception as e:
            raise VectorDBCollectionError(f"创建/获取 Collection 失败: {str(e)}")

    @property
    def collection(self) -> chromadb.Collection:
        """获取当前 Collection（懒加载）"""
        if self._collection is None:
            self._collection = self.get_or_create_collection()
        return self._collection

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(VectorDBError)
    )
    def health_check(self) -> HealthStatus:
        """
        健康检查

        Returns:
            HealthStatus: 健康状态信息
        """
        try:
            # 获取心跳
            heartbeat = self.client.heartbeat()

            # 获取所有 Collections
            collections = self.client.list_collections()
            collection_names = [c.name for c in collections]

            # 计算总文档数
            total_docs = sum(c.count() for c in collections)

            return HealthStatus(
                is_connected=True,
                version=chromadb.__version__,
                collections=collection_names,
                total_documents=total_docs,
                error_message=None,
                checked_at=datetime.now()
            )
        except Exception as e:
            return HealthStatus(
                is_connected=False,
                version=None,
                collections=[],
                total_documents=0,
                error_message=f"健康检查失败: {str(e)}",
                checked_at=datetime.now()
            )

    def add_document(
        self,
        document: Document,
        collection_name: Optional[str] = None
    ) -> bool:
        """
        添加单个文档

        Args:
            document: 文档对象
            collection_name: Collection 名称（可选）

        Returns:
            bool: 是否成功
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            # 准备数据
            ids = [document.id]
            documents = [document.content]
            # ChromaDB 不接受空的 metadata，如果为空则不传递
            metadatas = [document.metadata] if document.metadata else None
            embeddings = [document.embedding] if document.embedding else None

            # 添加到 ChromaDB
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings
            )

            logger.info(f"文档 {document.id} 添加成功")
            return True

        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise VectorDBInsertError(f"添加文档失败: {str(e)}")

    def add_documents(
        self,
        documents: List[Document],
        collection_name: Optional[str] = None,
        batch_size: int = 100
    ) -> BatchInsertResult:
        """
        批量添加文档

        Args:
            documents: 文档列表
            collection_name: Collection 名称（可选）
            batch_size: 批次大小

        Returns:
            BatchInsertResult: 批量插入结果
        """
        if not documents:
            return BatchInsertResult(
                success=True,
                inserted_count=0,
                failed_count=0
            )

        try:
            collection = self.get_or_create_collection(collection_name)

            inserted_count = 0
            failed_count = 0
            failed_ids = []

            # 分批处理
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                try:
                    # 准备批次数据
                    ids = [doc.id for doc in batch]
                    contents = [doc.content for doc in batch]
                    # 过滤空的 metadata
                    metadatas = [doc.metadata if doc.metadata else {"_placeholder": "true"} for doc in batch]
                    embeddings = [doc.embedding for doc in batch if doc.embedding]
                    embeddings = embeddings if len(embeddings) == len(batch) else None

                    # 批量添加
                    collection.add(
                        ids=ids,
                        documents=contents,
                        metadatas=metadatas,
                        embeddings=embeddings
                    )

                    inserted_count += len(batch)
                    logger.info(f"批次 {i//batch_size + 1} 插入成功: {len(batch)} 个文档")

                except Exception as e:
                    logger.error(f"批次 {i//batch_size + 1} 插入失败: {e}")
                    failed_count += len(batch)
                    failed_ids.extend([doc.id for doc in batch])

            return BatchInsertResult(
                success=failed_count == 0,
                inserted_count=inserted_count,
                failed_count=failed_count,
                failed_ids=failed_ids,
                error_message=None if failed_count == 0 else f"{failed_count} 个文档插入失败"
            )

        except Exception as e:
            logger.error(f"批量添加文档失败: {e}")
            raise VectorDBInsertError(f"批量添加文档失败: {str(e)}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(VectorDBQueryError)
    )
    def search(
        self,
        query: Optional[str] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> SearchResults:
        """
        向量相似度搜索

        Args:
            query: 查询文本（与 query_embeddings 二选一）
            query_embeddings: 查询向量（与 query 二选一）
            n_results: 返回结果数量
            where: 元数据过滤条件（如 {"source": "confluence"}）
            where_document: 文档内容过滤条件
            collection_name: Collection 名称（可选）

        Returns:
            SearchResults: 搜索结果
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            # 构建查询参数
            query_params = {
                "n_results": n_results,
                "where": where,
                "where_document": where_document,
                "include": ["documents", "metadatas", "distances"]
            }

            # 根据输入类型选择查询方式
            if query_embeddings is not None:
                query_params["query_embeddings"] = query_embeddings
                query_text = None
            elif query is not None:
                query_params["query_texts"] = [query]
                query_text = query
            else:
                raise ValueError("Either query or query_embeddings must be provided")

            # 执行查询
            results: QueryResult = collection.query(**query_params)

            # 解析结果
            search_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    distance = results["distances"][0][i] if results["distances"] else 0.0
                    # 将距离转换为相似度分数（1 - normalized_distance）
                    score = max(0.0, 1.0 - distance)

                    search_results.append(SearchResult(
                        id=results["ids"][0][i],
                        content=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] or {},
                        distance=distance,
                        score=score
                    ))

            return SearchResults(
                results=search_results,
                total=len(search_results),
                query=query if query else "[embedding query]",
                limit=n_results
            )

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            raise VectorDBQueryError(f"搜索失败: {str(e)}")

    def get_document(
        self,
        document_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[Document]:
        """
        根据 ID 获取文档

        Args:
            document_id: 文档 ID
            collection_name: Collection 名称（可选）

        Returns:
            Document: 文档对象，不存在返回 None
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            results: GetResult = collection.get(
                ids=[document_id],
                include=["documents", "metadatas", "embeddings"]
            )

            if not results["ids"]:
                return None

            # 处理 embeddings（可能是 None 或列表）
            embedding = None
            if results.get("embeddings") is not None and len(results["embeddings"]) > 0:
                embedding = results["embeddings"][0]

            return Document(
                id=results["ids"][0],
                content=results["documents"][0],
                metadata=results["metadatas"][0] or {},
                embedding=embedding
            )

        except Exception as e:
            logger.error(f"获取文档失败: {e}")
            raise VectorDBQueryError(f"获取文档失败: {str(e)}")

    def delete_document(
        self,
        document_id: str,
        collection_name: Optional[str] = None
    ) -> bool:
        """
        删除文档

        Args:
            document_id: 文档 ID
            collection_name: Collection 名称（可选）

        Returns:
            bool: 是否成功
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(ids=[document_id])
            logger.info(f"文档 {document_id} 删除成功")
            return True

        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False

    def delete_documents(
        self,
        where: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> int:
        """
        根据条件批量删除文档

        Args:
            where: 删除条件（如 {"source": "jira"}）
            collection_name: Collection 名称（可选）

        Returns:
            int: 删除的文档数量
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            # 先查询符合条件的文档数量
            results = collection.get(where=where, include=["documents"])
            count = len(results["ids"])

            # 执行删除
            if count > 0:
                collection.delete(where=where)
                logger.info(f"删除了 {count} 个文档")

            return count

        except Exception as e:
            logger.error(f"批量删除文档失败: {e}")
            return 0

    def get_collection_info(
        self,
        collection_name: Optional[str] = None
    ) -> CollectionInfo:
        """
        获取 Collection 信息

        Args:
            collection_name: Collection 名称（可选）

        Returns:
            CollectionInfo: Collection 信息
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            return CollectionInfo(
                name=collection.name,
                count=collection.count(),
                metadata=collection.metadata or {},
                embedding_function=str(self.embedding_function) if self.embedding_function else None
            )

        except Exception as e:
            logger.error(f"获取 Collection 信息失败: {e}")
            raise VectorDBCollectionError(f"获取 Collection 信息失败: {str(e)}")

    def list_collections(self) -> List[CollectionInfo]:
        """
        列出所有 Collections

        Returns:
            List[CollectionInfo]: Collection 信息列表
        """
        try:
            collections = self.client.list_collections()

            collection_infos = []
            for col in collections:
                collection_infos.append(CollectionInfo(
                    name=col.name,
                    count=col.count(),
                    metadata=col.metadata or {}
                ))

            return collection_infos

        except Exception as e:
            logger.error(f"列出 Collections 失败: {e}")
            raise VectorDBCollectionError(f"列出 Collections 失败: {str(e)}")

    def delete_collection(self, collection_name: str) -> bool:
        """
        删除 Collection

        Args:
            collection_name: Collection 名称

        Returns:
            bool: 是否成功
        """
        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' 删除成功")

            # 如果删除的是当前 Collection，重置
            if self._collection and self._collection.name == collection_name:
                self._collection = None

            return True

        except Exception as e:
            logger.error(f"删除 Collection 失败: {e}")
            return False

    def close(self) -> None:
        """关闭连接"""
        if self._client:
            self._client = None
            self._collection = None
            self._is_connected = False
            logger.info("ChromaDB 连接已关闭")

    def __enter__(self):
        """上下文管理器：进入"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器：退出"""
        self.close()


# 全局单例实例（可选）
_global_chroma_client: Optional[ChromaDBClient] = None


def get_chroma_client() -> ChromaDBClient:
    """
    获取全局 ChromaDB 客户端单例

    Returns:
        ChromaDBClient: ChromaDB 客户端实例
    """
    global _global_chroma_client
    if _global_chroma_client is None:
        _global_chroma_client = ChromaDBClient()
    return _global_chroma_client
