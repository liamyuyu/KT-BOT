# KT-BOT Examples

This directory contains example scripts demonstrating the usage of KT-BOT modules.

## Prerequisites

1. **Ollama is running**: Make sure Docker Desktop is running and Ollama container is started:
   ```bash
   docker-compose ps
   ```

2. **Model is downloaded**: Ensure qwen2.5:7b model is available:
   ```bash
   docker exec ktbot-ollama ollama list
   ```

3. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

## Available Examples

### test_llm.py - LLM Module Testing

Tests the LLM module functionality including:
- Health check for Ollama service
- Text generation (non-streaming)
- Chat conversation
- Streaming generation
- Text embedding (optional)

**Usage:**
```bash
python examples/test_llm.py
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════════╗
║               KT-BOT LLM Module Test                     ║
╚══════════════════════════════════════════════════════════╝

============================================================
1. Health Check
============================================================

ollama_service:
  Status: healthy
  version: 0.13.5
  ...
```

## Notes

- **Performance**: Since Ollama runs on CPU in Docker, inference is slower (~10-20 tokens/sec)
- **First run**: The first generation may take longer as the model loads into memory
- **Embedding**: To test embedding, download the model first:
  ```bash
  docker exec ktbot-ollama ollama pull bge-large-zh
  ```
