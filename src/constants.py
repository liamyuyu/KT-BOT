"""
KT-BOT Constants
项目常量定义
"""

# ========== Application ==========
APP_NAME = "KT-BOT"
APP_VERSION = "0.1.0"

# ========== Models ==========
DEFAULT_LLM_MODEL = "qwen2.5:latest"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"

# ========== Supported Models ==========
SUPPORTED_LLM_MODELS = [
    "qwen2.5:3b",
    "qwen2.5:7b",
    "qwen2.5:latest",
    "qwen2.5:14b",
    "llama3.1:8b",
    "mistral:7b",
]

SUPPORTED_EMBEDDING_MODELS = [
    "bge-large-zh",
    "nomic-embed-text",
    "mxbai-embed-large",
]

# ========== Vector Stores ==========
VECTOR_STORE_CHROMADB = "chromadb"
VECTOR_STORE_QDRANT = "qdrant"
VECTOR_STORE_MILVUS = "milvus"

# ========== File Extensions ==========
SUPPORTED_DOC_EXTENSIONS = [
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
    ".md",
    ".xlsx",
    ".xls",
]

# ========== Chunk Settings ==========
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50

# ========== Retrieval Settings ==========
DEFAULT_RETRIEVAL_K = 20
DEFAULT_RERANK_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.6

# ========== Timeouts ==========
OLLAMA_DEFAULT_TIMEOUT = 300
HTTP_REQUEST_TIMEOUT = 60
