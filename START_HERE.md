# 🚀 KT-BOT 开发快速开始 | Quick Start

> **最后更新**: 2026-01-16 (下午)
> **当前 Sprint**: Sprint 2 (2026-01-17 ~ 2026-01-30)
> **Sprint 1**: ✅ 100% 完成 (55/55 points)
> **Sprint 2 进度**: 🔄 59% 完成 (17/29 points) █████████████████░░░░░░░░░░░░
> **当前阶段**: Task 2.5 Reranker 模型集成完成，准备 Task 2.6

---

## 📍 当前位置 | Current Status

### ✅ 最新完成：Task 2.5 Reranker 模型集成 ⭐

**交付内容**:
- ✅ CrossEncoderReranker 实现（~91 行代码）
  - 延迟加载机制（按需加载模型）
  - 自动设备检测（CPU/CUDA/MPS）
  - 批量打分优化（batch_size 可配置）
  - Sigmoid 分数归一化（0-1 区间）
  - 完整的异步支持（asyncio.to_thread）
- ✅ 数据模型（RerankerConfig, RerankerResult）
- ✅ 14/14 单元测试通过（85.71% 覆盖率）
- ✅ 依赖安装（sentence-transformers, torch, numpy）

**技术亮点**:
- Cross-Encoder 模型集成（bge-reranker-large）
- 批量处理优化（减少推理次数）
- 延迟加载模型（节省内存）
- NumPy 兼容性修复（降级到 1.26.4）

**测试结果** ✅:
- ✅ 14 个单元测试全部通过
- ✅ 测试覆盖率：85.71%
- ✅ 所有功能验证通过

---

## 🎯 当前任务 | Current Task

### ⚡ Task 2.6 - 完整检索流程集成 (4 story points)

**状态**: ⏳ 待开始 - 所有依赖已完成

**依赖状态**:
- ✅ Task 2.1 - BM25 全文检索
- ✅ Task 2.2 - RRF 融合算法
- ✅ Task 2.3 - 检索性能优化
- ✅ Task 2.4 - API 和 UI 集成
- ✅ Task 2.5 - Reranker 模型集成

**任务目标**:
1. 更新 RAG Pipeline（Hybrid → Rerank → Top-K）
2. 添加重排序开关和参数（enable_reranking, rerank_top_k）
3. 更新 API 和 UI 支持重排序
4. 实现批量重排序优化
5. 添加重排序缓存机制
6. 创建端到端测试
7. 性能对比测试（开启/关闭重排序）

---

## ⏰ Sprint 2 时间规划 | Sprint 2 Timeline

**Sprint 2 周期**: 2026-01-17 ~ 2026-01-30（还剩 14 天）

**已完成任务** (17/29 points):
- ✅ 2026-01-16: Task 2.1-2.5 (混合检索 + Reranker)

**待完成任务** (12/29 points):
| 日期 | 任务 | 状态 | 故事点 |
|------|------|------|--------|
| 2026-01-17-18 | Task 2.6 完整检索流程集成 | ⏳ 下一个 | 4点 |
| 2026-01-19-20 | Task 2.7 文档管理后端 API | ⏳ 计划中 | 4点 |
| 2026-01-21-22 | Task 2.8 文档管理 UI 界面 | ⏳ 计划中 | 4点 |
| 2026-01-23-30 | Sprint 2 测试和文档 | ⏳ 计划中 | - |

---

## 🚀 三步快速启动 | 3-Step Quick Start

### 第 1 步：环境检查

```bash
# 进入项目
cd /Users/macbook/ai-project/KT-BOT

# 查看最新提交
git log --oneline -3

# 检查分支
git status
```

### 第 2 步：服务检查

```bash
# 检查 Ollama（Embedding 模型）
curl -s http://localhost:11434/api/tags | grep bge-large-zh

# 检查 ChromaDB
python -c "from src.core.vectordb import get_chroma_client; print(get_chroma_client().health_check())"

# 检查 Jira 连接
python -c "from src.integrations.jira import get_jira_client; import asyncio; client = get_jira_client(); print(asyncio.run(client.health_check()))"
```

### 第 3 步：测试 RAG 模块

**Task 1.5 已完成** ✅

```bash
# 运行 RAG 单元测试
pytest tests/unit/test_rag/test_chunker.py -v
# 12 passed in 2.34s

# 查看 RAG 模块
ls -lh src/core/rag/

# 测试模块导入
python -c "from src.core.rag import *; print('RAG module imported successfully')"

# 查看使用示例
cat examples/rag_example.py
```

### 第 4 步：开始 Task 1.7

**告诉 Claude**:
```
开始 Task 1.7 - Web UI 对话界面的开发。
需要实现基础对话界面，集成 LLM 和 RAG 检索功能。
```

---

## 📝 需求快速回顾 | Requirements Recap

### 实现范围：基础版 RAG

| 组件 | 实现内容 | 技术选择 |
|------|---------|---------|
| **数据源** | Jira Issues | 使用 JiraClient.fetch_issues() |
| **分块器** | 固定长度分块 | 500-1000 字符，100-200 重叠 |
| **向量化** | Ollama Embedding | bge-large-zh 模型，批量生成 |
| **存储** | ChromaDB | 使用 add_documents() 批量插入 |
| **检索** | 向量相似度搜索 | ChromaDB.search() |

### 模块清单

```
src/core/rag/
├── __init__.py           # 模块导出
├── models.py             # Chunk, IndexResult, RetrievalResult
├── exceptions.py         # RAGError, ChunkingError, IndexingError
├── chunker.py            # TextChunker（固定长度分块）
├── indexer.py            # DocumentIndexer（Jira → ChromaDB）
└── retriever/
    ├── __init__.py
    ├── base.py           # 检索器基类
    └── vector.py         # VectorRetriever（向量检索）
```

---

## 💡 关键技术点 | Technical Highlights

### Issue 内容组装

```python
def format_issue_content(issue: JiraIssue) -> str:
    """将 JiraIssue 转换为可索引的文本"""
    return f"""
Issue: {issue.key}
标题: {issue.summary}
类型: {issue.issue_type.name}
状态: {issue.status.name}
优先级: {issue.priority.name if issue.priority else 'N/A'}

描述:
{issue.description or '无'}

评论:
{format_comments(issue.comments)}

标签: {', '.join(issue.labels)}
"""
```

### 文档分块策略

```python
class TextChunker:
    def __init__(self, chunk_size=800, overlap=150):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[Chunk]:
        """固定长度分块，带重叠"""
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            chunks.append(Chunk(
                content=chunk_text,
                chunk_index=chunk_index,
                ...
            ))

            start += (self.chunk_size - self.overlap)
            chunk_index += 1

        return chunks
```

### 批量 Embedding 生成

```python
from src.core.llm import get_llm_manager

async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """批量生成 embeddings"""
    manager = get_llm_manager()
    embedding_model = manager.create_embedding()  # bge-large-zh

    responses = await embedding_model.embed_batch(texts)
    return [resp.embedding for resp in responses]
```

---

## 🔍 已完成的探索结果 | Exploration Results

### Jira 集成

**位置**: `src/integrations/jira/`

**关键 API**:
```python
from src.integrations.jira import get_jira_client

client = get_jira_client()

# 批量查询
page = client.fetch_issues(
    project_key="PROJ",
    max_results=100,
    start_at=0
)

for issue in page.issues:
    print(f"{issue.key}: {issue.summary}")
```

**JiraIssue 字段**:
- `summary`: 标题
- `description`: 描述（可能为空）
- `comments`: 评论列表
- `labels`: 标签列表
- `status`, `priority`, `issue_type`: 分类信息

### ChromaDB 集成

**位置**: `src/core/vectordb/`

**关键 API**:
```python
from src.core.vectordb import ChromaDBClient, Document

client = ChromaDBClient(
    persist_directory="./data/chroma",
    collection_name="jira_issues"
)

# 批量添加
docs = [
    Document(
        id="PROJ-123_chunk_0",
        content="...",
        metadata={"issue_key": "PROJ-123", "chunk_index": 0}
    )
]
result = client.add_documents(docs, batch_size=100)

# 向量搜索
results = client.search("查询文本", n_results=10)
```

### LLM/Embedding 模块

**位置**: `src/core/llm/`

**关键 API**:
```python
from src.core.llm import get_llm_manager

manager = get_llm_manager()
embedding = manager.create_embedding()  # bge-large-zh

# 单个 embedding
response = await embedding.embed("文本内容")
print(len(response.embedding))  # 1024 维

# 批量 embedding
responses = await embedding.embed_batch(["文本1", "文本2"])
```

---

## 📚 相关文档 | Documentation

### 必读文档

1. **`BOOKMARK.md`** - 详细的开发进度书签（本文件的详细版）
2. **`docs/SPRINT1_TASK1.6_CHROMADB.md`** (1,435行) - ChromaDB 集成详解
3. **`SPRINTS.md`** - Sprint 1 任务清单和进度
4. **`examples/test_chroma.py`** - ChromaDB 使用示例
5. **`examples/test_jira.py`** - Jira 集成示例

### 代码参考

- **Jira Models**: `src/integrations/jira/models.py`
- **Jira Client**: `src/integrations/jira/client.py`
- **ChromaDB Client**: `src/core/vectordb/chroma_client.py`
- **ChromaDB Models**: `src/core/vectordb/models.py`
- **LLM Manager**: `src/core/llm/manager.py`
- **Ollama Embedding**: `src/core/llm/ollama.py`

---

## 🐛 已知问题 | Known Issues

### ChromaDB 相关

1. **空元数据问题** ✅ 已解决
   - 单文档：使用 `None`
   - 批量：使用占位符 `{"_placeholder": "true"}`

2. **NumPy 数组判断** ✅ 已解决
   ```python
   # ✅ 正确
   if results.get("embeddings") is not None and len(results["embeddings"]) > 0:
       embedding = results["embeddings"][0]
   ```

3. **测试隔离问题** ⚠️ 非阻塞
   - `test_list_collections` 偶尔失败
   - 不影响功能，仅测试隔离问题

---

## 🎯 成功标准 | Success Criteria

### Task 1.5 - 基础文档索引 ✅ 已完成

- [x] 能够从 Jira 批量获取 Issues
- [x] 能够将 Issue 内容分块（800字符，150重叠）
- [x] 能够生成 embeddings（使用 bge-large-zh）
- [x] 能够存储到 ChromaDB（带元数据）
- [x] 能够进行向量检索（返回相关 chunks）
- [x] 单元测试覆盖率 > 90%（达到 95%+）
- [x] 集成测试通过（完整流程）
- [x] 示例代码可运行

### Task 1.7 - Web UI 对话界面（待完成）

- [ ] 基础对话界面（输入 + 消息列表）
- [ ] LLM 对话生成功能
- [ ] RAG 检索增强功能
- [ ] 流式响应显示
- [ ] UI 样式和交互

---

## 📞 快速命令 | Quick Commands

```bash
# 运行测试
pytest tests/unit/test_rag/test_chunker.py -v     # RAG 单元测试 ⭐
python examples/rag_example.py                     # RAG 使用示例 ⭐

# 代码覆盖率
pytest tests/unit/test_rag/ --cov=src/core/rag --cov-report=html

# 验证 RAG 模块
python -c "from src.core.rag import *; print('RAG module OK')"

# 查看代码统计
find src/core/rag -name "*.py" -exec wc -l {} + | tail -1

# Git 操作
git status                                         # 查看状态
git log --oneline -5                               # 最近提交
git add . && git commit -m "feat: RAG module"     # 提交代码
```

---

## 💬 与 Claude 对话的建议

### 开始 Task 1.7 - Web UI 对话界面

```
开始 Task 1.7 - Web UI 对话界面的开发。

需要实现：
1. 基础对话界面（输入框 + 消息列表）
2. 集成 LLM 进行对话生成（使用 OllamaLLM）
3. 集成 RAG 检索增强回答（使用 VectorRetriever）
4. 实现流式响应显示
5. 添加简单的 UI 样式

技术要求：
- 使用现有的 LLMManager 和 RAG 模块
- 支持流式响应（chat_stream）
- 集成向量检索增强上下文
- 遵循现有项目模式
```

### 查看 RAG 模块实现

```
查看 Task 1.5 完成的 RAG 模块实现：
1. 文本分块器的实现细节
2. 文档索引器的工作流程
3. 向量检索器的使用方法
4. 查看使用示例
```

### 测试 RAG 功能

```
运行 RAG 模块的测试和示例：
1. 运行单元测试
2. 运行使用示例
3. 测试索引和检索流程
```

---

**快速开始指南更新时间**: 2026-01-12
**下次更新**: 完成 Task 1.7 后

**🎯 Sprint 1 进度：90.9% (50/55 points) - 还剩 4 天！**
