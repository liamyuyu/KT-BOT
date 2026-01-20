"""
文档管理服务 - 处理文档的 CRUD 和索引
"""
import logging
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict

from src.core.rag import TextChunker, ChunkingConfig
from src.core.vectordb import get_chroma_client, ChromaDBClient
from src.core.llm.manager import get_llm_manager
from ..schemas.document import (
    DocumentMetadata, DocumentDetail, DocumentListResponse,
    DocumentUploadRequest, DocumentUpdateRequest, DocumentQueryRequest,
    DocumentUploadResponse, DocumentDeleteResponse, DocumentStatsResponse
)

logger = logging.getLogger(__name__)


class DocumentService:
    """文档管理服务"""

    def __init__(
        self,
        chunker: Optional[TextChunker] = None,
        vectordb_client: Optional[ChromaDBClient] = None
    ):
        """
        初始化文档管理服务

        Args:
            chunker: 文本分块器
            vectordb_client: 向量数据库客户端
        """
        self.chunker = chunker or TextChunker(
            config=ChunkingConfig(chunk_size=800, chunk_overlap=150)
        )
        self.vectordb_client = vectordb_client or get_chroma_client()
        self.llm_manager = get_llm_manager()
        self.embedding_model = None  # Lazy load

        # 文档元数据存储（使用 ChromaDB 的 metadata）
        self._metadata_key_prefix = "doc_meta_"

        logger.info("DocumentService initialized")

    def _generate_document_id(
        self,
        title: str,
        source_type: str,
        source_id: Optional[str] = None
    ) -> str:
        """
        生成文档ID

        Args:
            title: 文档标题
            source_type: 来源类型
            source_id: 来源ID

        Returns:
            文档ID
        """
        if source_id:
            # 使用 source_type + source_id
            return f"{source_type}_{source_id}"
        else:
            # 使用标题哈希
            hash_input = f"{title}_{datetime.now().isoformat()}"
            hash_value = hashlib.md5(hash_input.encode()).hexdigest()[:12]
            return f"{source_type}_{hash_value}"

    async def upload_document(
        self,
        request: DocumentUploadRequest
    ) -> DocumentUploadResponse:
        """
        上传并索引文档

        Args:
            request: 文档上传请求

        Returns:
            上传响应

        Raises:
            ValueError: 参数无效
            RuntimeError: 索引失败
        """
        logger.info(f"Uploading document: {request.title}")

        # 生成文档ID
        document_id = self._generate_document_id(
            request.title,
            request.source_type,
            request.source_id
        )

        # 检查文档是否已存在
        existing = await self.get_document_by_id(document_id)
        if existing:
            logger.warning(f"Document {document_id} already exists, will overwrite")
            # 先删除旧文档
            await self.delete_document(document_id)

        # 文本分块
        chunks = self.chunker.chunk_text(
            text=request.content,
            parent_id=document_id
        )
        logger.info(f"Split document into {len(chunks)} chunks")

        # 准备元数据
        doc_metadata = {
            "document_id": document_id,
            "title": request.title,
            "source_type": request.source_type,
            "source_id": request.source_id or "",
            "content_preview": request.content[:200],
            "chunk_count": len(chunks),
            "indexed_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "tags": ",".join(request.tags),  # 存储为逗号分隔字符串
            **request.metadata  # 合并额外元数据
        }

        # 为每个 chunk 添加文档级元数据
        for chunk in chunks:
            chunk.metadata.update({
                "document_id": document_id,
                "title": request.title,
                "source_type": request.source_type,
                **doc_metadata  # 所有元数据都存储在chunk中
            })

        # 批量索引到 ChromaDB
        try:
            # Lazy load embedding model
            if self.embedding_model is None:
                self.embedding_model = self.llm_manager.create_embedding()
                logger.info(f"Embedding model loaded: {self.embedding_model.model_name}")

            # 生成 embeddings
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = await self.embedding_model.embed_batch(chunk_texts)

            # 准备数据
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            chunk_metadatas = [chunk.metadata for chunk in chunks]

            # 获取 collection
            collection = self.vectordb_client.get_or_create_collection(
                self.vectordb_client.collection_name
            )

            # 批量添加到 ChromaDB
            collection.add(
                ids=chunk_ids,
                documents=chunk_texts,
                embeddings=embeddings,
                metadatas=chunk_metadatas
            )

            logger.info(f"Indexed {len(chunks)} chunks for document {document_id}")

        except Exception as e:
            logger.error(f"Failed to index document: {e}", exc_info=True)
            raise RuntimeError(f"Document indexing failed: {e}")

        indexed_at = datetime.now()

        return DocumentUploadResponse(
            document_id=document_id,
            title=request.title,
            chunk_count=len(chunks),
            indexed_at=indexed_at,
            message=f"Document '{request.title}' uploaded and indexed successfully"
        )

    async def get_document_list(
        self,
        query: DocumentQueryRequest
    ) -> DocumentListResponse:
        """
        获取文档列表

        Args:
            query: 查询请求

        Returns:
            文档列表响应
        """
        logger.info(f"Getting document list with query: {query.model_dump()}")

        try:
            # 从 ChromaDB 获取所有文档的元数据
            # ChromaDB 的 get() 方法可以获取所有文档
            collection = self.vectordb_client.get_or_create_collection(
                self.vectordb_client.collection_name
            )

            # 获取所有数据
            results = collection.get(
                limit=10000,  # 获取足够多的数据
                include=["metadatas"]
            )

            if not results or not results.get("metadatas"):
                return DocumentListResponse(
                    documents=[],
                    total=0,
                    limit=query.limit,
                    offset=query.offset
                )

            # 从 chunk 元数据中提取文档信息
            doc_map: Dict[str, DocumentMetadata] = {}

            for metadata in results["metadatas"]:
                if not metadata or "document_id" not in metadata:
                    continue

                doc_id = metadata["document_id"]

                # 跳过已处理的文档
                if doc_id in doc_map:
                    # 更新 chunk_count
                    doc_map[doc_id].chunk_count += 1
                    continue

                # 筛选：source_type
                if query.source_type and metadata.get("source_type") != query.source_type:
                    continue

                # 筛选：tags
                if query.tags:
                    doc_tags = metadata.get("tags", "").split(",")
                    doc_tags = [t.strip() for t in doc_tags if t.strip()]
                    if not any(tag in doc_tags for tag in query.tags):
                        continue

                # 筛选：search_text
                if query.search_text:
                    title = metadata.get("title", "")
                    preview = metadata.get("content_preview", "")
                    if (query.search_text.lower() not in title.lower() and
                            query.search_text.lower() not in preview.lower()):
                        continue

                # 解析时间
                try:
                    indexed_at = datetime.fromisoformat(metadata.get("indexed_at", datetime.now().isoformat()))
                    created_at = datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat()))
                    updated_at = datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat()))
                except (ValueError, TypeError):
                    indexed_at = created_at = updated_at = datetime.now()

                # 解析 tags
                tags_str = metadata.get("tags", "")
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]

                # 创建文档元数据
                doc_map[doc_id] = DocumentMetadata(
                    document_id=doc_id,
                    title=metadata.get("title", ""),
                    source_type=metadata.get("source_type", "local"),
                    source_id=metadata.get("source_id") or None,
                    content_preview=metadata.get("content_preview", ""),
                    chunk_count=1,  # 初始为1，后续会累加
                    indexed_at=indexed_at,
                    created_at=created_at,
                    updated_at=updated_at,
                    tags=tags,
                    metadata={k: v for k, v in metadata.items()
                             if k not in ["document_id", "title", "source_type",
                                          "source_id", "content_preview", "indexed_at",
                                          "created_at", "updated_at", "tags"]}
                )

            # 转换为列表并排序
            documents = list(doc_map.values())
            documents.sort(key=lambda x: x.indexed_at, reverse=True)

            total = len(documents)

            # 应用分页
            documents = documents[query.offset:query.offset + query.limit]

            logger.info(f"Found {total} documents, returning {len(documents)}")

            return DocumentListResponse(
                documents=documents,
                total=total,
                limit=query.limit,
                offset=query.offset
            )

        except Exception as e:
            logger.error(f"Failed to get document list: {e}", exc_info=True)
            return DocumentListResponse(
                documents=[],
                total=0,
                limit=query.limit,
                offset=query.offset
            )

    async def get_document_by_id(self, document_id: str) -> Optional[DocumentDetail]:
        """
        根据ID获取文档详情

        Args:
            document_id: 文档ID

        Returns:
            文档详情，不存在则返回 None
        """
        logger.info(f"Getting document by ID: {document_id}")

        try:
            collection = self.vectordb_client.get_or_create_collection(
                self.vectordb_client.collection_name
            )

            # 查询该文档的所有 chunks
            results = collection.get(
                where={"document_id": document_id},
                include=["documents", "metadatas"]
            )

            if not results or not results.get("metadatas"):
                logger.warning(f"Document {document_id} not found")
                return None

            metadatas = results["metadatas"]
            documents_content = results["documents"]
            chunk_ids = results["ids"]

            # 从第一个 chunk 获取文档元数据
            first_metadata = metadatas[0]

            # 重建完整内容
            full_content = "\n".join(documents_content)

            # 解析时间
            try:
                indexed_at = datetime.fromisoformat(first_metadata.get("indexed_at", datetime.now().isoformat()))
                created_at = datetime.fromisoformat(first_metadata.get("created_at", datetime.now().isoformat()))
                updated_at = datetime.fromisoformat(first_metadata.get("updated_at", datetime.now().isoformat()))
            except (ValueError, TypeError):
                indexed_at = created_at = updated_at = datetime.now()

            # 解析 tags
            tags_str = first_metadata.get("tags", "")
            tags = [t.strip() for t in tags_str.split(",") if t.strip()]

            return DocumentDetail(
                document_id=document_id,
                title=first_metadata.get("title", ""),
                content=full_content,
                source_type=first_metadata.get("source_type", "local"),
                source_id=first_metadata.get("source_id") or None,
                chunk_count=len(chunk_ids),
                chunks=chunk_ids,
                indexed_at=indexed_at,
                created_at=created_at,
                updated_at=updated_at,
                tags=tags,
                metadata={k: v for k, v in first_metadata.items()
                         if k not in ["document_id", "title", "source_type",
                                      "source_id", "indexed_at", "created_at",
                                      "updated_at", "tags", "content_preview", "chunk_count"]}
            )

        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}", exc_info=True)
            return None

    async def delete_document(self, document_id: str) -> DocumentDeleteResponse:
        """
        删除文档及其所有chunks

        Args:
            document_id: 文档ID

        Returns:
            删除响应

        Raises:
            ValueError: 文档不存在
        """
        logger.info(f"Deleting document: {document_id}")

        try:
            collection = self.vectordb_client.get_or_create_collection(
                self.vectordb_client.collection_name
            )

            # 查询该文档的所有 chunks
            results = collection.get(
                where={"document_id": document_id}
            )

            if not results or not results.get("ids"):
                raise ValueError(f"Document {document_id} not found")

            chunk_ids = results["ids"]
            deleted_count = len(chunk_ids)

            # 删除所有 chunks
            collection.delete(ids=chunk_ids)

            logger.info(f"Deleted {deleted_count} chunks for document {document_id}")

            return DocumentDeleteResponse(
                document_id=document_id,
                deleted_chunks=deleted_count,
                message=f"Document '{document_id}' and {deleted_count} chunks deleted successfully"
            )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}", exc_info=True)
            raise RuntimeError(f"Document deletion failed: {e}")

    async def get_document_stats(self) -> DocumentStatsResponse:
        """
        获取文档统计信息

        Returns:
            统计响应
        """
        logger.info("Getting document statistics")

        try:
            collection = self.vectordb_client.get_or_create_collection(
                self.vectordb_client.collection_name
            )

            # 获取所有元数据
            results = collection.get(
                limit=10000,
                include=["metadatas"]
            )

            if not results or not results.get("metadatas"):
                return DocumentStatsResponse(
                    total_documents=0,
                    total_chunks=0,
                    by_source_type={},
                    by_tags={},
                    indexed_at_range=None
                )

            metadatas = results["metadatas"]
            total_chunks = len(metadatas)

            # 统计
            doc_ids = set()
            by_source_type = defaultdict(int)
            by_tags = defaultdict(int)
            indexed_times = []

            for metadata in metadatas:
                if not metadata:
                    continue

                doc_id = metadata.get("document_id")
                if doc_id:
                    doc_ids.add(doc_id)

                source_type = metadata.get("source_type", "unknown")
                by_source_type[source_type] += 1

                tags_str = metadata.get("tags", "")
                tags = [t.strip() for t in tags_str.split(",") if t.strip()]
                for tag in tags:
                    by_tags[tag] += 1

                try:
                    indexed_at = datetime.fromisoformat(metadata.get("indexed_at", ""))
                    indexed_times.append(indexed_at)
                except (ValueError, TypeError):
                    pass

            # 计算索引时间范围
            indexed_at_range = None
            if indexed_times:
                indexed_at_range = {
                    "earliest": min(indexed_times),
                    "latest": max(indexed_times)
                }

            total_documents = len(doc_ids)

            logger.info(
                f"Stats: {total_documents} documents, {total_chunks} chunks"
            )

            return DocumentStatsResponse(
                total_documents=total_documents,
                total_chunks=total_chunks,
                by_source_type=dict(by_source_type),
                by_tags=dict(by_tags),
                indexed_at_range=indexed_at_range
            )

        except Exception as e:
            logger.error(f"Failed to get document stats: {e}", exc_info=True)
            return DocumentStatsResponse(
                total_documents=0,
                total_chunks=0,
                by_source_type={},
                by_tags={}
            )


# 全局单例
_document_service: Optional[DocumentService] = None


def get_document_service(
    chunker: Optional[TextChunker] = None,
    vectordb_client: Optional[ChromaDBClient] = None
) -> DocumentService:
    """
    获取文档服务单例

    Args:
        chunker: 文本分块器
        vectordb_client: 向量数据库客户端

    Returns:
        DocumentService 实例
    """
    global _document_service

    if _document_service is None:
        _document_service = DocumentService(chunker, vectordb_client)

    return _document_service
