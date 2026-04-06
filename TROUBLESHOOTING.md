# KT-BOT Troubleshooting Guide

## Issues Fixed (2026-04-06)

### 1. Ollama Model Name Mismatch ✅

**Problem:**
```
HTTP Request: POST http://localhost:11434/api/chat "HTTP/1.1 404 Not Found"
```

**Root Cause:**
The configuration file specified `qwen2.5:7b`, but the actual model in Ollama is named `qwen2.5:latest` (which is the 7.6B version).

**Fix Applied:**
Updated `src/config.py` to use the correct model name:
```python
ollama_model: str = Field(
    default="qwen2.5:latest",  # Changed from "qwen2.5:7b"
    description="默认对话模型"
)
```

### 2. BM25 Model Not Initialized ✅

**Problem:**
```
RetrievalError: BM25 model not initialized. Call index_documents() first.
```

**Root Cause:**
The hybrid retriever uses both vector (ChromaDB) and BM25 retrievers. While ChromaDB had indexed documents, the BM25 retriever was never initialized with those documents.

**Fixes Applied:**

1. **Created initialization script** (`scripts/init_bm25.py`):
   - Loads all documents from ChromaDB
   - Indexes them into BM25 retriever
   - Saves the BM25 index to disk for persistence

2. **Updated FastAPI startup** (`src/api/main.py`):
   - Automatically loads BM25 index on startup if it exists
   - Shows helpful warning if BM25 index is missing

3. **Added graceful fallback** (`src/api/services/chat_service.py`):
   - If BM25 is not initialized, automatically falls back to vector-only retrieval
   - Logs a helpful message explaining how to enable hybrid search

## How to Use

### Starting the Application

Simply run:
```bash
python src/main.py
```

The application will:
1. Load the BM25 index automatically (if it exists)
2. Fall back to vector-only retrieval if BM25 is not available
3. Show clear messages about the retrieval method being used

### Reinitializing BM25 Index

If you add new documents to ChromaDB and need to update the BM25 index:

```bash
python scripts/init_bm25.py
```

This will:
- Load all documents from ChromaDB
- Rebuild the BM25 index
- Save it to `data/bm25_cache/bm25_index.pkl`

### Checking Available Models

To see which Ollama models you have installed:
```bash
curl http://localhost:11434/api/tags
```

To verify Ollama is running:
```bash
curl http://localhost:11434/api/version
```

## Current Status

✅ **BM25 Index**: Initialized with 1 document
✅ **Ollama Model**: Using `qwen2.5:latest` (7.6B)
✅ **ChromaDB**: Connected with data in `./data/chroma`
✅ **Hybrid Retrieval**: Ready to use

## Retrieval Methods

The application supports three retrieval methods:

1. **Vector** - Uses ChromaDB semantic search only
2. **BM25** - Uses BM25 keyword search only (requires initialization)
3. **Hybrid** - Combines both methods for best results (requires BM25 initialization)

If BM25 is not initialized, hybrid retrieval will automatically fall back to vector-only mode.

## Common Issues

### Ollama Service Not Running

**Symptoms:**
```
Connection refused to localhost:11434
```

**Solution:**
Start Ollama service:
```bash
ollama serve
```

### Model Not Found

**Symptoms:**
```
HTTP 404 Not Found
```

**Solution:**
Pull the required model:
```bash
ollama pull qwen2.5:latest
ollama pull nomic-embed-text
```

### No Documents in ChromaDB

**Symptoms:**
```
No documents found in ChromaDB collection
```

**Solution:**
Index some documents first (e.g., from Jira):
```bash
python scripts/index_documents.py
```

## Architecture Notes

### Retrieval Pipeline

```
User Query
    ↓
[RAG Enabled?]
    ↓ Yes
[Retrieval Method]
    ↓
┌──────────┬──────────┬──────────┐
│  Vector  │   BM25   │  Hybrid  │
└──────────┴──────────┴──────────┘
    ↓          ↓          ↓
[ChromaDB] [BM25]  [Both → Fusion]
    ↓          ↓          ↓
[Optional Reranking]
    ↓
[Context Assembly]
    ↓
[LLM Generation]
    ↓
Response
```

### Storage Locations

- **ChromaDB**: `./data/chroma/`
- **BM25 Index**: `./data/bm25_cache/bm25_index.pkl`
- **Logs**: `./logs/`
- **Config**: `.env` (optional) or defaults in `src/config.py`
