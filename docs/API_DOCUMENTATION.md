# KT-BOT API 文档

> **版本**: v0.1.0
> **最后更新**: 2026-01-16
> **基础 URL**: `http://localhost:7860/api/v1`

---

## 目录

- [概述](#概述)
- [认证](#认证)
- [API 端点](#api-端点)
  - [健康检查](#健康检查)
  - [对话接口](#对话接口)
  - [模型管理](#模型管理)
- [数据模型](#数据模型)
- [错误处理](#错误处理)
- [使用示例](#使用示例)

---

## 概述

KT-BOT API 提供基于 RAG（检索增强生成）的智能对话服务。通过 RESTful API，您可以：

- 发起智能对话（支持流式和非流式）
- 管理对话历史
- 查询可用模型
- 监控系统健康状态

### 技术栈

- **框架**: FastAPI 0.109+
- **协议**: HTTP/1.1, Server-Sent Events (SSE)
- **数据格式**: JSON
- **流式传输**: SSE (text/event-stream)

---

## 认证

**当前版本（v0.1.0）不需要认证**。

未来版本将支持：
- JWT Bearer Token
- API Key
- OAuth 2.0

---

## API 端点

### 健康检查

#### GET `/health`

检查 API 服务健康状态。

**请求**:
```http
GET /api/v1/health HTTP/1.1
Host: localhost:7860
```

**响应 200 OK**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-01-16T12:00:00Z",
  "services": {
    "llm": "healthy",
    "vectordb": "healthy",
    "session_manager": "healthy"
  }
}
```

**字段说明**:
- `status`: 服务状态 (`healthy` | `unhealthy`)
- `version`: API 版本号
- `timestamp`: 响应时间戳（ISO 8601）
- `services`: 各子服务健康状态

---

### 对话接口

#### POST `/chat/message`

发起非流式对话（适用于一次性获取完整响应）。

**请求**:
```http
POST /api/v1/chat/message HTTP/1.1
Host: localhost:7860
Content-Type: application/json

{
  "message": "如何在 Kubernetes 中配置存储类？",
  "session_id": "session-123",
  "model_name": "qwen2.5:7b",
  "enable_rag": true,
  "rag_top_k": 3,
  "temperature": 0.7
}
```

**请求参数**:
| 字段 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| `message` | string | ✓ | - | 用户消息内容 |
| `session_id` | string | ✗ | null | 会话 ID（不提供则自动创建）|
| `model_name` | string | ✗ | "qwen2.5:7b" | LLM 模型名称 |
| `enable_rag` | boolean | ✗ | true | 是否启用 RAG 检索 |
| `rag_top_k` | integer | ✗ | 3 | RAG 检索文档数量 (1-10) |
| `temperature` | float | ✗ | 0.7 | 生成温度 (0.0-2.0) |

**响应 200 OK**:
```json
{
  "session_id": "session-123",
  "message": {
    "role": "assistant",
    "content": "在 Kubernetes 中配置存储类（StorageClass）的步骤如下...\n\n---\n\n### 📚 参考来源\n\n**[1] JIRA Issue: PROJ-001** - Kubernetes 存储配置 (相关度: 95%)\n**[2] Confluence Page** - K8s 最佳实践文档 (相关度: 87%)\n\n> 💡 回答基于以上文档内容生成",
    "timestamp": "2026-01-16T12:00:00Z"
  },
  "retrieved_contexts": [
    {
      "chunk_id": "PROJ-001_chunk_0",
      "content": "# Kubernetes 存储类配置\n\nStorageClass 是 K8s 中定义存储类型的资源...",
      "score": 0.95,
      "source": {
        "source_type": "jira_issue",
        "issue_key": "PROJ-001",
        "project_key": "PROJ",
        "title": "Kubernetes 存储配置"
      }
    }
  ],
  "model_name": "qwen2.5:7b",
  "token_count": 256,
  "duration_ms": 1234
}
```

**响应字段**:
- `session_id`: 会话 ID（用于后续对话）
- `message`: 助手消息对象
  - `role`: 消息角色（固定为 "assistant"）
  - `content`: 消息内容（Markdown 格式，包含 RAG 来源）
  - `timestamp`: 消息时间戳
- `retrieved_contexts`: RAG 检索结果列表（仅在 `enable_rag=true` 时返回）
  - `chunk_id`: 文档块 ID
  - `content`: 文档块内容
  - `score`: 相关度分数 (0.0-1.0)
  - `source`: 来源信息
- `model_name`: 使用的模型名称
- `token_count`: 生成的 Token 数量
- `duration_ms`: 生成耗时（毫秒）

---

#### POST `/chat/stream`

发起流式对话（实时接收响应，打字机效果）。

**请求**:
```http
POST /api/v1/chat/stream HTTP/1.1
Host: localhost:7860
Content-Type: application/json
Accept: text/event-stream

{
  "message": "如何在 Kubernetes 中配置存储类？",
  "session_id": "session-123",
  "model_name": "qwen2.5:7b",
  "enable_rag": true,
  "rag_top_k": 3,
  "temperature": 0.7
}
```

**响应 200 OK** (Server-Sent Events):
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: start
data: {"session_id": "session-123"}

event: context
data: {"contexts": [...RAG检索结果...]}

event: token
data: {"content": "在 "}

event: token
data: {"content": "Kubernetes "}

event: token
data: {"content": "中"}

...

event: end
data: {"model": "qwen2.5:7b", "token_count": 256, "duration_ms": 1234}
```

**事件类型**:

| 事件 | 说明 | 数据格式 |
|------|------|----------|
| `start` | 开始生成 | `{"session_id": "xxx"}` |
| `context` | RAG 检索结果 | `{"contexts": [...]}` |
| `token` | 生成的文本片段 | `{"content": "text"}` |
| `end` | 生成结束 | `{"model": "xxx", "token_count": 123, "duration_ms": 1234}` |
| `error` | 错误 | `{"message": "error message"}` |

**客户端示例** (JavaScript):
```javascript
const eventSource = new EventSource('/api/v1/chat/stream');

eventSource.addEventListener('token', (event) => {
  const data = JSON.parse(event.data);
  console.log(data.content);  // 实时显示文本
});

eventSource.addEventListener('end', (event) => {
  const data = JSON.parse(event.data);
  console.log('生成完成:', data);
  eventSource.close();
});
```

---

#### GET `/chat/history/{session_id}`

获取会话历史记录。

**请求**:
```http
GET /api/v1/chat/history/session-123 HTTP/1.1
Host: localhost:7860
```

**响应 200 OK**:
```json
{
  "session_id": "session-123",
  "messages": [
    {
      "role": "user",
      "content": "如何配置 Kubernetes？",
      "timestamp": "2026-01-16T11:58:00Z"
    },
    {
      "role": "assistant",
      "content": "配置 Kubernetes 的步骤如下...",
      "timestamp": "2026-01-16T11:58:05Z"
    }
  ],
  "created_at": "2026-01-16T11:58:00Z",
  "updated_at": "2026-01-16T12:00:00Z",
  "message_count": 10
}
```

**响应 404 Not Found** (会话不存在):
```json
{
  "detail": "Session not found: session-123"
}
```

---

#### DELETE `/chat/history/{session_id}`

清空会话历史。

**请求**:
```http
DELETE /api/v1/chat/history/session-123 HTTP/1.1
Host: localhost:7860
```

**响应 200 OK**:
```json
{
  "session_id": "session-123",
  "status": "deleted",
  "message": "History cleared successfully"
}
```

**响应 404 Not Found**:
```json
{
  "detail": "Session not found: session-123"
}
```

---

### 模型管理

#### GET `/models/list`

获取可用的 LLM 模型列表。

**请求**:
```http
GET /api/v1/models/list HTTP/1.1
Host: localhost:7860
```

**响应 200 OK**:
```json
{
  "models": [
    {
      "name": "qwen2.5:7b",
      "type": "llm",
      "size": "7B",
      "description": "Qwen 2.5 中文大模型（7B 参数）",
      "recommended": true
    },
    {
      "name": "qwen2.5:14b",
      "type": "llm",
      "size": "14B",
      "description": "Qwen 2.5 中文大模型（14B 参数）",
      "recommended": false
    },
    {
      "name": "llama3.1:8b",
      "type": "llm",
      "size": "8B",
      "description": "LLaMA 3.1 英文模型（8B 参数）",
      "recommended": false
    }
  ],
  "default_model": "qwen2.5:7b",
  "embedding_model": "bge-large-zh"
}
```

---

#### GET `/models/status`

获取模型服务状态。

**请求**:
```http
GET /api/v1/models/status HTTP/1.1
Host: localhost:7860
```

**响应 200 OK**:
```json
{
  "ollama_status": "running",
  "ollama_url": "http://localhost:11434",
  "active_models": [
    {
      "name": "qwen2.5:7b",
      "loaded": true,
      "size_bytes": 4500000000,
      "last_used": "2026-01-16T12:00:00Z"
    }
  ],
  "embedding_model": {
    "name": "bge-large-zh",
    "loaded": true,
    "dimensions": 1024
  }
}
```

---

## 数据模型

### ChatMessage

```python
{
  "role": "user" | "assistant" | "system",
  "content": str,  # 消息内容（支持 Markdown）
  "timestamp": str  # ISO 8601 格式
}
```

### ChatRequest

```python
{
  "message": str,  # 必需
  "session_id": Optional[str],
  "model_name": Optional[str] = "qwen2.5:7b",
  "enable_rag": Optional[bool] = True,
  "rag_top_k": Optional[int] = 3,  # 1-10
  "temperature": Optional[float] = 0.7  # 0.0-2.0
}
```

### ChatResponse

```python
{
  "session_id": str,
  "message": ChatMessage,
  "retrieved_contexts": Optional[List[RetrievedContext]],
  "model_name": str,
  "token_count": int,
  "duration_ms": int
}
```

### RetrievedContext

```python
{
  "chunk_id": str,
  "content": str,  # 文档块内容
  "score": float,  # 相关度分数 (0.0-1.0)
  "source": {
    "source_type": "jira_issue" | "confluence_page" | ...,
    "issue_key": Optional[str],
    "project_key": Optional[str],
    "title": str,
    ...  # 其他来源特定字段
  }
}
```

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误示例

**400 Bad Request** - 参数错误:
```json
{
  "detail": "Invalid rag_top_k: must be between 1 and 10"
}
```

**422 Unprocessable Entity** - 验证失败:
```json
{
  "detail": [
    {
      "loc": ["body", "message"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error** - 服务器错误:
```json
{
  "detail": "LLM generation failed: connection timeout"
}
```

---

## 使用示例

### Python (httpx)

#### 非流式对话

```python
import httpx
import asyncio

async def chat_example():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:7860/api/v1/chat/message",
            json={
                "message": "如何部署 Kubernetes？",
                "enable_rag": True,
                "rag_top_k": 3
            }
        )
        data = response.json()
        print(f"助手: {data['message']['content']}")
        print(f"会话 ID: {data['session_id']}")

asyncio.run(chat_example())
```

#### 流式对话

```python
import httpx
import asyncio
import json

async def stream_chat_example():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:7860/api/v1/chat/stream",
            json={"message": "什么是 FastAPI？"},
            timeout=30.0
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if response.headers.get("event") == "token":
                        print(data["content"], end="", flush=True)

asyncio.run(stream_chat_example())
```

### JavaScript (Fetch API)

#### 非流式对话

```javascript
async function chatExample() {
  const response = await fetch('http://localhost:7860/api/v1/chat/message', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      message: '如何部署 Kubernetes？',
      enable_rag: true,
      rag_top_k: 3
    })
  });

  const data = await response.json();
  console.log('助手:', data.message.content);
  console.log('会话 ID:', data.session_id);
}

chatExample();
```

#### 流式对话

```javascript
function streamChatExample() {
  const eventSource = new EventSource(
    'http://localhost:7860/api/v1/chat/stream?message=什么是FastAPI'
  );

  let fullText = '';

  eventSource.addEventListener('token', (event) => {
    const data = JSON.parse(event.data);
    fullText += data.content;
    console.log(fullText);  // 实时更新显示
  });

  eventSource.addEventListener('end', (event) => {
    const data = JSON.parse(event.data);
    console.log('生成完成:', data);
    eventSource.close();
  });

  eventSource.addEventListener('error', (event) => {
    console.error('错误:', event);
    eventSource.close();
  });
}

streamChatExample();
```

### cURL

#### 非流式对话

```bash
curl -X POST http://localhost:7860/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "如何部署 Kubernetes？",
    "enable_rag": true,
    "rag_top_k": 3
  }'
```

#### 流式对话

```bash
curl -N -X POST http://localhost:7860/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": "什么是 FastAPI？"
  }'
```

#### 获取历史

```bash
curl http://localhost:7860/api/v1/chat/history/session-123
```

#### 清空历史

```bash
curl -X DELETE http://localhost:7860/api/v1/chat/history/session-123
```

---

## 性能建议

### 优化 RAG 检索

1. **调整 `rag_top_k`**:
   - 较少文档（1-3）：响应更快，但可能错过相关信息
   - 较多文档（5-10）：更全面，但耗时更长

2. **使用流式响应**:
   - 对于需要实时反馈的场景，使用 `/chat/stream`
   - 可以更早开始显示响应，提升用户体验

3. **会话复用**:
   - 保存 `session_id` 并在后续请求中使用
   - 避免重复加载历史消息

### 并发限制

- 当前版本默认最大并发请求数：**10**
- 超过限制时将返回 503 Service Unavailable
- 流式请求会占用一个连接直到完成

---

## 更新日志

### v0.1.0 (2026-01-16)

**新增功能**:
- ✨ 非流式对话接口 (`/chat/message`)
- ✨ 流式对话接口 (`/chat/stream`)
- ✨ 会话历史管理 (`/chat/history`)
- ✨ 模型查询接口 (`/models/list`, `/models/status`)
- ✨ 健康检查接口 (`/health`)
- ✨ RAG 检索增强生成
- ✨ 会话管理（30分钟 TTL）

**已知限制**:
- 暂不支持认证
- 暂不支持多租户
- 会话数据存储在内存和本地文件（非分布式）

---

## 联系和支持

- **GitHub**: [KT-BOT Repository](https://github.com/yourusername/KT-BOT)
- **文档**: [完整文档](../README.md)
- **问题反馈**: [GitHub Issues](https://github.com/yourusername/KT-BOT/issues)

---

**© 2026 KT-BOT Team. All rights reserved.**
