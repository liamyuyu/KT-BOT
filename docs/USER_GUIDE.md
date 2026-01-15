# KT-BOT 使用指南

> **版本**: v0.1.0
> **最后更新**: 2026-01-16
> **适用于**: 开发者、系统管理员、最终用户

---

## 目录

- [快速开始](#快速开始)
- [启动服务](#启动服务)
- [使用 Web UI](#使用-web-ui)
- [使用 API](#使用-api)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)

---

## 快速开始

### 前提条件

确保已安装以下软件：

1. **Python 3.10+**
   ```bash
   python --version
   ```

2. **Ollama 服务**（本地 LLM）
   ```bash
   # 检查 Ollama 是否运行
   curl http://localhost:11434/api/tags
   ```

3. **必要依赖**
   ```bash
   pip install -r requirements.txt
   ```

### 5 分钟快速体验

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/KT-BOT.git
cd KT-BOT

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动 Ollama（如果未运行）
ollama serve &

# 4. 拉取推荐模型
ollama pull qwen2.5:7b
ollama pull bge-large-zh

# 5. 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件，配置 Jira/Confluence（可选）

# 6. 启动 KT-BOT
python src/main.py
```

**完成！** 现在访问：
- **Gradio UI**: http://localhost:7861
- **FastAPI Docs**: http://localhost:7860/docs

---

## 启动服务

### 方式 1: 一键启动（推荐）

```bash
python src/main.py
```

这将自动启动：
- **FastAPI 后端** (端口 7860)
- **Gradio 前端** (端口 7861)

### 方式 2: 分别启动

#### 启动 FastAPI 后端

```bash
# 终端 1: 后端
uvicorn src.api.main:app --host 0.0.0.0 --port 7860 --reload
```

#### 启动 Gradio 前端

```bash
# 终端 2: 前端
python src/ui/app.py
```

### 验证启动成功

1. **检查 FastAPI 健康**:
   ```bash
   curl http://localhost:7860/api/v1/health
   ```

   预期输出：
   ```json
   {
     "status": "healthy",
     "version": "0.1.0",
     ...
   }
   ```

2. **访问 Gradio UI**:
   打开浏览器访问 http://localhost:7861

---

## 使用 Web UI

### 界面概览

```
┌─────────────────────────────────────────────────────────┐
│  🤖 KT-BOT - 企业知识库智能助手                         │
├─────────────────────────────────────┬───────────────────┤
│                                     │  ⚙️ 设置          │
│  💬 对话历史                        │                   │
│  ┌────────────────────────────┐    │  LLM 模型:        │
│  │ User: 如何部署 K8s？       │    │  [qwen2.5:7b] ▼  │
│  │ Bot: 部署 K8s 的步骤如下...│    │                   │
│  └────────────────────────────┘    │  ☑ 启用 RAG 检索  │
│                                     │  检索文档数量: 3   │
│  ┌────────────────────────────┐    │  生成温度: 0.7     │
│  │ 请输入您的问题...           │    │                   │
│  │                            │    │  🗑️ 清空对话      │
│  └────────────────────────────┘    │                   │
│              [发送]                 │  状态: 就绪        │
│                                     │                   │
│  💡 示例问题:                       │                   │
│  • JIRA 中如何创建新的工作项？     │                   │
│  • 如何配置项目的权限设置？        │                   │
└─────────────────────────────────────┴───────────────────┘
```

### 基本操作

#### 1. 发起对话

1. 在输入框中输入您的问题
2. 按 Enter 或点击"发送"按钮
3. 等待 AI 生成回答（支持实时流式显示）

**示例**:
```
用户: 如何在 Kubernetes 中配置持久化存储？

助手: 在 Kubernetes 中配置持久化存储需要以下步骤：

1. 创建 StorageClass...
2. 创建 PersistentVolumeClaim...
...

---
### 📚 参考来源
[1] JIRA Issue: PROJ-123 - K8s 存储配置 (相关度: 95%)
```

#### 2. 调整设置

**LLM 模型选择**:
- `qwen2.5:7b`: 中文优化，速度快（推荐）
- `qwen2.5:14b`: 更高准确率，需更多内存
- `llama3.1:8b`: 英文模型

**RAG 检索**:
- **启用 RAG**: 打开以使用知识库检索
- **检索文档数量**: 控制参考文档数量（1-10）
  - 1-3: 快速，精准
  - 5-10: 全面，但较慢

**生成温度**:
- **0.0-0.5**: 严谨，确定性强
- **0.7**: 平衡（推荐）
- **1.0-2.0**: 创造性，多样性强

#### 3. 查看来源引用

每个回答底部会显示参考来源：

```markdown
### 📚 参考来源

**[1] JIRA Issue: PROJ-123** - Kubernetes 存储配置 (相关度: 95%)
**[2] Confluence Page** - K8s 最佳实践 (相关度: 87%)

> 💡 回答基于以上文档内容生成
```

点击来源链接可跳转到原始文档（未来版本）。

#### 4. 清空对话

点击"🗑️ 清空对话"按钮清除当前会话历史，开始新对话。

---

## 使用 API

### 通过 API 集成 KT-BOT

适用场景：
- 自定义前端应用
- 集成到现有系统
- 自动化脚本
- 移动应用

### 基本示例

#### Python 客户端

```python
import httpx
import asyncio

class KTBotClient:
    def __init__(self, base_url="http://localhost:7860"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1"
        self.session_id = None

    async def chat(self, message, enable_rag=True):
        """发起对话"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/chat/message",
                json={
                    "message": message,
                    "session_id": self.session_id,
                    "enable_rag": enable_rag,
                    "rag_top_k": 3
                },
                timeout=30.0
            )
            data = response.json()

            # 保存会话 ID
            self.session_id = data["session_id"]

            return data

    async def chat_stream(self, message, callback):
        """流式对话"""
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.api_url}/chat/stream",
                json={"message": message, "session_id": self.session_id},
                timeout=30.0
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        import json
                        event_data = json.loads(line[6:])
                        await callback(event_data)

# 使用示例
async def main():
    client = KTBotClient()

    # 非流式对话
    result = await client.chat("如何部署 Kubernetes？")
    print(result["message"]["content"])

    # 流式对话
    async def on_token(data):
        if "content" in data:
            print(data["content"], end="", flush=True)

    await client.chat_stream("什么是 FastAPI？", on_token)

asyncio.run(main())
```

#### JavaScript 客户端

```javascript
class KTBotClient {
  constructor(baseURL = 'http://localhost:7860') {
    this.baseURL = baseURL;
    this.apiURL = `${baseURL}/api/v1`;
    this.sessionId = null;
  }

  async chat(message, enableRAG = true) {
    const response = await fetch(`${this.apiURL}/chat/message`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        message,
        session_id: this.sessionId,
        enable_rag: enableRAG,
        rag_top_k: 3
      })
    });

    const data = await response.json();
    this.sessionId = data.session_id;
    return data;
  }

  chatStream(message, onToken, onEnd) {
    const eventSource = new EventSource(
      `${this.apiURL}/chat/stream?message=${encodeURIComponent(message)}`
    );

    eventSource.addEventListener('token', (event) => {
      const data = JSON.parse(event.data);
      onToken(data.content);
    });

    eventSource.addEventListener('end', (event) => {
      const data = JSON.parse(event.data);
      onEnd(data);
      eventSource.close();
    });

    return eventSource;
  }
}

// 使用示例
const client = new KTBotClient();

// 非流式对话
const result = await client.chat('如何部署 Kubernetes？');
console.log(result.message.content);

// 流式对话
client.chatStream(
  '什么是 FastAPI？',
  (token) => console.log(token),
  (stats) => console.log('完成:', stats)
);
```

更多 API 详情请参考 [API 文档](./API_DOCUMENTATION.md)。

---

## 配置说明

### 环境变量配置

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env`:

```env
# ===== Ollama 配置 =====
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_EMBEDDING_MODEL=bge-large-zh

# ===== Jira 集成（可选）=====
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token

# ===== Confluence 集成（可选）=====
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_confluence_api_token

# ===== 向量数据库 =====
VECTOR_STORE=chromadb
VECTOR_STORE_PATH=./data/chroma

# ===== 应用配置 =====
API_PORT=7860
GRADIO_PORT=7861
LOG_LEVEL=INFO
```

### 获取 Jira/Confluence API Token

1. 登录 Atlassian 账号
2. 访问 [API Tokens 页面](https://id.atlassian.com/manage-profile/security/api-tokens)
3. 点击"Create API token"
4. 输入标签名称（如"KT-BOT"）
5. 复制 Token 并保存到 `.env`

### 模型配置

#### 安装 Ollama 模型

```bash
# 推荐模型（中文）
ollama pull qwen2.5:7b       # 主 LLM（8GB 内存）
ollama pull bge-large-zh     # Embedding 模型

# 可选模型
ollama pull qwen2.5:14b      # 更大模型（16GB 内存）
ollama pull llama3.1:8b      # 英文模型
```

#### 切换模型

**方式 1**: 通过 UI 切换
- 在 Gradio 界面的"LLM 模型"下拉菜单中选择

**方式 2**: 修改 `.env`
```env
OLLAMA_MODEL=qwen2.5:14b
```

**方式 3**: API 请求中指定
```python
response = await client.post(
    "/api/v1/chat/message",
    json={"message": "...", "model_name": "llama3.1:8b"}
)
```

---

## 常见问题

### 启动问题

#### Q1: Ollama 连接失败

**错误**:
```
httpx.ConnectError: All connection attempts failed
```

**解决方案**:
```bash
# 1. 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 2. 如果未运行，启动 Ollama
ollama serve

# 3. 验证模型已安装
ollama list
```

#### Q2: 端口被占用

**错误**:
```
OSError: [Errno 48] Address already in use
```

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :7860
lsof -i :7861

# 杀死进程
kill -9 <PID>

# 或修改端口
export API_PORT=8860
export GRADIO_PORT=8861
python src/main.py
```

#### Q3: 模块导入错误

**错误**:
```
ModuleNotFoundError: No module named 'gradio'
```

**解决方案**:
```bash
# 重新安装依赖
pip install -r requirements.txt

# 或安装特定模块
pip install gradio>=4.16.0
```

### 使用问题

#### Q4: 响应速度慢

**优化建议**:

1. **使用更小的模型**:
   ```env
   OLLAMA_MODEL=qwen2.5:7b  # 而非 14b
   ```

2. **减少 RAG 检索数量**:
   ```python
   {"rag_top_k": 2}  # 默认是 3
   ```

3. **使用 GPU 加速**:
   ```bash
   # 确保 Ollama 使用 GPU
   ollama serve --gpu
   ```

4. **启用流式响应**:
   使用 `/chat/stream` 而非 `/chat/message`

#### Q5: RAG 检索不准确

**优化建议**:

1. **增加检索数量**:
   ```python
   {"rag_top_k": 5}  # 默认是 3
   ```

2. **检查文档是否已索引**:
   ```python
   # 手动索引文档
   python scripts/index_documents.py
   ```

3. **调整相似度阈值**（高级）:
   编辑 `config/retrieval.yaml`:
   ```yaml
   retrieval:
     similarity_threshold: 0.5  # 降低阈值
   ```

#### Q6: 内存不足

**解决方案**:

1. **使用更小的模型**:
   ```bash
   ollama pull qwen2.5:7b  # 8GB
   # 而非 qwen2.5:32b  # 32GB
   ```

2. **限制并发请求**:
   ```env
   MAX_CONCURRENT_REQUESTS=2
   ```

3. **清理缓存**:
   ```bash
   rm -rf data/chroma/cache
   ```

### API 问题

#### Q7: CORS 错误

**错误**:
```
Access to fetch at '...' from origin '...' has been blocked by CORS policy
```

**解决方案**:
FastAPI 已配置 CORS，允许所有来源。如需限制：

编辑 `src/api/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 限制来源
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Q8: 会话丢失

**原因**: 会话数据存储在内存和本地文件，重启服务会丢失内存中的会话。

**解决方案**:
会话数据会自动持久化到 `./data/chat_history/` 目录，重启后会自动加载。

---

## 最佳实践

### 提问技巧

#### ✅ 好的提问

```
具体、明确的问题：
- "如何在 Kubernetes 中配置持久化存储类？"
- "FastAPI 的依赖注入是如何工作的？"
- "PostgreSQL 连接池的推荐配置参数是什么？"

带上下文的问题：
- "我们的项目使用 SQLAlchemy，如何配置连接池？"
- "在生产环境部署 K8s 时，网络插件应该选择哪个？"
```

#### ❌ 避免的提问

```
过于宽泛的问题：
- "怎么用 Kubernetes？"（太宽泛，改为：如何部署 Kubernetes 集群？）
- "Python 怎么写？"（太宽泛，改为：FastAPI 如何实现异步处理？）

没有上下文的问题：
- "这个怎么配置？"（什么？改为明确说明）
- "为什么报错？"（什么错误？提供错误信息）
```

### RAG 使用建议

1. **启用 RAG 的场景**:
   - 查询项目文档和规范
   - 询问团队知识和经验
   - 需要引用来源的回答

2. **禁用 RAG 的场景**:
   - 通用编程问题
   - 理论知识解释
   - 不需要项目特定信息的问题

3. **调整 RAG 参数**:
   ```
   高精度场景：rag_top_k = 1-2
   平衡场景：rag_top_k = 3-5
   高召回场景：rag_top_k = 7-10
   ```

### 会话管理

1. **长对话建议**:
   - 定期清空历史（避免上下文过长）
   - 保存重要对话（导出功能，未来版本）

2. **多主题对话**:
   - 不同主题使用不同会话
   - 清空历史后开始新主题

### 性能优化

1. **首次启动优化**:
   ```bash
   # 预加载模型（首次启动会慢）
   ollama pull qwen2.5:7b
   ollama pull bge-large-zh

   # 预热模型
   ollama run qwen2.5:7b "hello"
   ```

2. **生产环境部署**:
   ```bash
   # 使用 Gunicorn + Uvicorn Workers
   gunicorn src.api.main:app \
     -w 4 \
     -k uvicorn.workers.UvicornWorker \
     --bind 0.0.0.0:7860
   ```

3. **缓存策略**:
   - 相同查询会从缓存返回
   - 缓存 TTL: 15 分钟（可配置）

---

## 进阶使用

### 自定义数据源

#### 索引自定义文档

```python
from src.core.rag.indexer import DocumentIndexer
from src.integrations.jira.models import JiraIssue

# 创建索引器
indexer = DocumentIndexer(jira_client=None)

# 准备文档（示例）
issues = [
    JiraIssue(
        issue_id="DOC-001",
        issue_key="DOC-001",
        summary="自定义文档标题",
        description="文档内容...",
        ...
    )
]

# 索引文档
result = await indexer.index_jira_issues(
    issues=issues,
    collection_name="custom_docs"
)

print(f"索引完成: {result.success_count} 个文档")
```

### 集成到现有系统

#### Webhook 集成

```python
from fastapi import FastAPI, Request
from src.api.services import get_chat_service

app = FastAPI()

@app.post("/webhook/chat")
async def chat_webhook(request: Request):
    """接收外部系统的对话请求"""
    data = await request.json()

    chat_service = get_chat_service()
    response = await chat_service.chat(
        message=data["message"],
        session_id=data.get("user_id"),
        enable_rag=True
    )

    return {
        "reply": response.message.content,
        "sources": response.retrieved_contexts
    }
```

---

## 获取帮助

### 文档资源

- **README**: [项目概览](../README.md)
- **API 文档**: [API 参考](./API_DOCUMENTATION.md)
- **开发指南**: [DEVELOPMENT.md](./DEVELOPMENT.md)

### 社区支持

- **GitHub Issues**: [报告问题](https://github.com/yourusername/KT-BOT/issues)
- **GitHub Discussions**: [讨论和提问](https://github.com/yourusername/KT-BOT/discussions)

### 联系我们

- **邮箱**: ktbot@example.com
- **Discord**: [加入社区](https://discord.gg/ktbot)

---

**祝您使用愉快！🎉**

**© 2026 KT-BOT Team**
