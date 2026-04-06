"""
Initialize BM25 Retriever with existing ChromaDB documents
Run this script to index existing documents from ChromaDB into BM25
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.vectordb.chroma_client import get_chroma_client
from src.core.rag.retriever.bm25 import get_bm25_retriever
from src.core.rag.models import Chunk
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def init_bm25_from_chroma():
    """
    Load documents from ChromaDB and index them in BM25 retriever
    """
    try:
        logger.info("Initializing BM25 retriever from ChromaDB...")

        # 1. Get ChromaDB client
        chroma_client = get_chroma_client()
        collection_name = settings.chroma_collection_name

        logger.info(f"Loading documents from ChromaDB collection: {collection_name}")

        # 2. Get all documents from ChromaDB
        # Note: ChromaDB's get() without IDs returns all documents
        try:
            result = chroma_client.collection.get(
                include=["documents", "metadatas"]
            )

            if not result or not result["ids"]:
                logger.warning("No documents found in ChromaDB collection")
                return False

            logger.info(f"Found {len(result['ids'])} documents in ChromaDB")

        except Exception as e:
            logger.error(f"Failed to load documents from ChromaDB: {e}")
            return False

        # 3. Convert ChromaDB documents to Chunk objects
        chunks = []
        for i, doc_id in enumerate(result["ids"]):
            content = result["documents"][i] if result["documents"] else ""
            metadata = result["metadatas"][i] if result["metadatas"] else {}

            chunk = Chunk(
                chunk_id=doc_id,
                parent_id=metadata.get("parent_id", doc_id),
                content=content,
                metadata=metadata,
                chunk_index=metadata.get("chunk_index", 0),
                start_index=metadata.get("start_index", 0),
                end_index=metadata.get("end_index", len(content))
            )
            chunks.append(chunk)

        logger.info(f"Converted {len(chunks)} documents to Chunk objects")

        # 4. Get BM25 retriever and index documents
        bm25_retriever = get_bm25_retriever()

        logger.info("Indexing documents in BM25...")
        bm25_retriever.index_documents(chunks)

        # 5. Save BM25 index to disk for persistence
        logger.info("Saving BM25 index to disk...")
        bm25_retriever.save_index()

        # 6. Verify index
        stats = bm25_retriever.get_statistics()
        logger.info(f"BM25 index statistics: {stats}")

        logger.info("✅ BM25 initialization completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to initialize BM25: {e}", exc_info=True)
        return False


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("BM25 Initialization Script")
    logger.info("=" * 60)

    success = asyncio.run(init_bm25_from_chroma())

    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✅ BM25 initialization completed successfully")
        logger.info("You can now use hybrid retrieval with BM25")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.error("\n" + "=" * 60)
        logger.error("❌ BM25 initialization failed")
        logger.error("Please check the errors above")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
