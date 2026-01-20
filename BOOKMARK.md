# 🔖 开发进度书签 | Development Bookmark

> **最后更新**: 2026-01-20
> **当前 Sprint**: Sprint 2 (2026-01-17 ~ 2026-01-30)
> **Sprint 1**: ✅ 全部完成 (55/55 故事点)
> **Sprint 2 进度**: 🔄 59% 完成 (17/29 故事点)
> **当前阶段**: 测试覆盖率提升完成 ✅（Jira: 97.28%, Confluence: 91.37%），准备开始 Task 2.6

---

## 🎯 当前状态 | Current Status

### ✅ Sprint 1 - 已完成任务 (55/55 故事点，100% ✅)

| 任务 | Story | 状态 | 完成日期 | 交付 |
|------|-------|------|----------|------|
| Task 1.1 | Ollama 模型初始化 (5点) | ✅ | 2026-01-03 | ~1,216 行代码 |
| Task 1.2 | 多模型管理 (8点) | ✅ | 2026-01-03 | 与 Task 1.1 并行 |
| Task 1.3 | Jira API 集成 (8点) | ✅ | 2026-01-05 | ~1,400 行代码 |
| Task 1.4 | Confluence API 集成 (8点) | ✅ | 2026-01-12 | ~2,050 行代码 |
| Task 1.6 | ChromaDB 配置 (8点) | ✅ | 2026-01-12 | ~2,136 行代码 |
| Task 1.5 | 基础文档索引 (13点) | ✅ | 2026-01-12 | ~1,181 行代码 |
| Task 1.7 | **Web UI 对话界面 (5点)** | ✅ | 2026-01-16 | ~2,200 行代码 + 文档 |

**最新提交**:
```bash
# Task 1.7 - Web UI 对话界面（100% 完成）✅

✅ FastAPI 后端 API（Phase 1 - 全部完成）
   - Phase 1.1: 数据模型和路由框架
     → 8 个 Pydantic v2 数据模型
     → 3 个 API 路由模块
     → FastAPI 应用入口（生命周期、CORS、异常处理）

   - Phase 1.2: 会话管理器
     → SessionManager（内存缓存 + JSON 持久化）
     → TTL 30分钟 + 容量限制 100 条消息

   - Phase 1.3: 对话服务（非流式）
     → ChatService 核心业务逻辑
     → LLM + RAG + SessionManager 集成

   - Phase 1.4: 流式响应（SSE）
     → ChatService.chat_stream() 实现
     → Server-Sent Events 完整支持
     → 5 种事件类型（start, context, token, end, error）

✅ Gradio 前端 UI（Phase 2 - 全部完成）
   - Phase 2.1: 基础布局
     → ChatPage 完整实现（436 行）
     → UI 组件（Chatbot, Textbox, Button, Dropdown, Slider）
     → 示例问题 + 配置面板

   - Phase 2.2: API 客户端
     → ChatAPIClient 完整实现（240 行）
     → 支持非流式和流式对话
     → SSE 事件流解析

   - Phase 2.3: 事件处理
     → 流式响应实时更新（打字机效果）
     → 会话状态管理（gr.State）
     → 历史清空功能

   - Phase 2.4: UI 优化 ✨ 新增
     → Markdown 渲染支持（render_markdown=True）
     → 代码高亮（VS Code Dark 主题）
     → RAG 来源引用自动格式化
     → 增强的 CSS 样式（按钮动画、输入框焦点效果）
     → LaTeX 数学公式支持
     → UI 布局优化：设置面板移至左侧，对话区域在右侧
     → Gradio 6.x 兼容性修复（移除弃用参数）

✅ 端到端集成（Phase 3 - 全部完成）
   - Phase 3.1: 主程序入口（src/main.py）
     → threading 并发启动 FastAPI + Gradio
     → FastAPI 后端（端口 7860）
     → Gradio 前端（端口 7861）

   - Phase 3.2-3.3: 测试和验证 ✨ 新增
     → 创建 RAG 端到端测试脚本
     → 5 个测试场景（索引、检索、过滤、语义搜索、边界情况）
     → 测试代码覆盖核心功能

✅ 文档和测试（Phase 4 - 全部完成）✨ 新增
   - Phase 4.1: 单元测试
     → 端到端测试脚本（tests/e2e/test_rag_simple.py）
     → 测试数据准备和验证逻辑

   - Phase 4.2: API 文档
     → 完整的 API 文档（docs/API_DOCUMENTATION.md）
     → 7 个 API 端点详细说明
     → 请求/响应示例（Python、JavaScript、cURL）
     → 数据模型定义和错误处理

   - Phase 4.3: 使用说明
     → 用户指南（docs/USER_GUIDE.md）
     → 快速开始、配置说明、常见问题
     → 最佳实践和进阶使用
     → 故障排除指南

# 代码统计
- 已创建文件: 24 个
  - 后端: 16 个文件（~1,100 行）
  - 前端: 7 个文件（~800 行）
  - 主程序: src/main.py（~120 行）
- 可用 API: 7/7 个端点全部实现 ✅
- **总计**: ~2,200 行代码

# 启动方式
python src/main.py
# → FastAPI: http://localhost:7860/docs
# → Gradio: http://localhost:7861
```

**Sprint 1 进度条**:
```
██████████████████████████████ 100% (55/55 points) ✅ COMPLETE!
```

---

### 🔄 Sprint 2 - 进行中任务 (17/29 故事点，59% 🔄)

| 任务 | Story | 状态 | 完成日期 | 交付 |
|------|-------|------|----------|------|
| Task 2.1 | BM25 全文检索 (4点) | ✅ | 2026-01-16 | ~436 行代码，9 测试 |
| Task 2.2 | RRF 融合算法 (3点) | ✅ | 2026-01-16 | ~632 行代码，13 测试 |
| Task 2.3 | 检索性能优化 (3点) | ✅ | 2026-01-16 | 并发检索+缓存 |
| Task 2.4 | API 和 UI 集成 (3点) | ✅ | 2026-01-16 | ~650 行代码，12 测试 |
| Task 2.5 | **Reranker 模型集成 (4点)** | ✅ | 2026-01-16 | ~384 行代码，14 测试 |
| Task 2.5.1 | **测试覆盖率提升 (额外任务)** | ✅ | 2026-01-20 | Jira: 97.28%, Confluence: 91.37% |
| Task 2.6 | 完整检索流程集成 (4点) | ⏳ | - | 待开始 |
| Task 2.7 | 文档管理后端 API (4点) | ⏳ | - | 待开始 |
| Task 2.8 | 文档管理 UI 界面 (4点) | ⏳ | - | 待开始 |

**最新提交**:
```bash
# Task 2.5.1 - 测试覆盖率提升（100% 完成）✅ 新增

✅ Jira 集成测试优化（78.91% → 97.28%）
   - 修复 5 个失败测试
     → timeout 参数默认值问题
     → Mock 对象字段类型问题
     → 配置初始化测试问题
     → API 错误异常类型问题
     → RetryError 处理问题

   - 新增 10 个测试用例
     → 错误处理测试（403, 500, 通用异常）
     → JQL 查询测试
     → 默认项目配置测试
     → 复杂 Issue 解析测试（组件、版本、优先级、分配人等）
     → API 错误重试机制测试
     → 日期时间解析错误测试
     → 客户端关闭测试

   - 测试结果
     → 64/64 测试通过（100%）
     → 覆盖率: 97.28%（147 语句，4 个未覆盖）
     → 未覆盖行: src/integrations/jira/client.py:151-152, 238-239

✅ Confluence 集成测试优化（80.94% → 91.37%）
   - 新增 11 个测试用例
     → 连接错误测试（500, 通用异常）
     → 复杂页面解析测试（祖先、标签、附件、版本、历史）
     → 最小字段页面测试（默认值处理）
     → 默认空间配置测试
     → CQL 查询回退测试
     → fetch_page_by_id 错误测试（404, 500）
     → fetch_page_by_title 测试
     → get_all_spaces API 错误测试
     → 限流处理测试（429）
     → 通用异常重试测试
     → 客户端关闭和上下文管理器测试

   - 测试结果
     → 64/64 测试通过（100%）
     → 覆盖率: 91.37%（278 语句，24 个未覆盖）
     → 未覆盖行: src/integrations/confluence/client.py:181-182, 198, 等

✅ 应用启动修复
   - 日志目录自动创建（src/main.py, src/ui/app.py）
   - .env 配置文件创建
   - Pydantic v2 protected_namespaces 警告修复
   - 端口占用进程清理（kill 32634）

# 代码统计
- 测试文件修改: 2 个
  - tests/unit/test_jira/test_client.py: +10 测试（54→64）
  - tests/unit/test_confluence/test_client.py: +11 测试（53→64）
- 源代码修复: 5 个文件
  - src/integrations/jira/client.py: timeout 参数修复
  - src/main.py: 日志目录修复
  - src/ui/app.py: 日志目录修复
  - src/api/schemas/chat.py: Pydantic 警告修复
  - src/core/rag/models.py: Pydantic 警告修复
- **总计**: 193 个测试全部通过

# Task 2.5 - Reranker 模型集成（100% 完成）✅

✅ 依赖安装
   - sentence-transformers 5.2.0
   - torch 2.2.2
   - numpy 1.26.4（兼容性修复）

✅ 数据模型（src/core/rag/models.py）
   - RerankerConfig: 重排序配置（8 个参数）
   - RerankerResult: 重排序结果（保留排名变化）

✅ CrossEncoderReranker 实现（src/core/rag/reranker/）
   - cross_encoder.py: 91 行核心代码
   - 延迟加载机制（首次使用时加载模型）
   - 自动设备检测（CPU/CUDA/MPS）
   - 批量打分优化（batch_size 可配置）
   - Sigmoid 分数归一化（0-1 区间）
   - 完整的异步支持（asyncio.to_thread）

✅ 单元测试（tests/unit/test_rag/test_reranker.py）
   - 14 个测试用例全部通过
   - 测试覆盖率: 85.71%
   - 测试重排序功能、批量处理、分数归一化等

# 代码统计
- 已创建文件: 3 个
  - 核心模块: src/core/rag/reranker/cross_encoder.py（91 行）
  - 模块导出: src/core/rag/reranker/__init__.py
  - 单元测试: tests/unit/test_rag/test_reranker.py（293 行）
- 数据模型更新: RerankerConfig, RerankerResult
- **总计**: ~384 行新代码

# 关键特性
1. Cross-Encoder 模型集成（bge-reranker-large）
2. 批量处理优化（batch_size=4）
3. 延迟加载（节省内存）
4. 完整的错误处理和日志记录
5. 高测试覆盖率（85.71%）
```

**Sprint 2 进度条**:
```
█████████████████░░░░░░░░░░░░░ 59% (17/29 points) 🔄 IN PROGRESS
```

---

## 🔄 下一步任务 | Next Task

### 🎯 **Task 2.6: 完整检索流程集成** (4点, 预计 2 天)

**目标**: 将 HybridRetriever 和 CrossEncoderReranker 组合成完整的 RAG Pipeline

**任务清单**:
- [ ] 更新 RAG Pipeline（Hybrid → Rerank → Top-K）
- [ ] 添加重排序开关和参数
- [ ] 更新 API 和 UI 支持重排序
- [ ] 实现批量重排序优化
- [ ] 添加重排序缓存机制
- [ ] 创建端到端测试
- [ ] 性能对比测试（开启/关闭重排序）

**预期交付**:
- 更新的 ChatService 集成重排序
- API 新增参数（enable_reranking, rerank_top_k）
- UI 新增重排序控制面板
- E2E 测试脚本
- 性能对比报告

---

## 🎉 已完成里程碑

### 🎊 **Sprint 1 已完成！**

所有任务（55/55 故事点）已交付完成，包括：

✅ Task 1.1-1.2: Ollama 模型集成和管理
✅ Task 1.3-1.4: Jira 和 Confluence API 集成
✅ Task 1.5-1.6: RAG 文档索引和 ChromaDB
✅ Task 1.7: Web UI 对话界面（含完整文档）

### 📋 Sprint 2 规划建议

**Epic 3 & 9**: RAG 检索优化
- 混合检索（向量 + BM25）
- Cross-Encoder 重排序
- 查询改写和扩展

**Epic 4**: Web UI 增强
- 高级对话功能（多轮、上下文）
- 文档管理界面
- 统计和监控仪表盘

**Epic 5**: MCP 协议集成
- MCP Server 实现
- 自定义 Tools 开发
- 与 Claude Desktop 集成

具体规划请参考 `SPRINTS.md`

---

## 📋 待完成任务 | Remaining Tasks

### 🎊 Sprint 1: 全部完成！

**Sprint 1 进度**: ✅ 55/55 故事点全部交付

**Sprint 1 状态**: ✅✅✅ 完成！

**交付物**:
- 7 个完整的任务模块
- ~10,000+ 行生产代码
- 3 个综合文档（API、用户指南、测试脚本）
- 完整可运行的 MVP 系统

---

## 💡 技术要点记录 | Technical Notes

### ChromaDB 集成关键点 (Task 1.6)

1. **空元数据处理**：
   - ChromaDB 不接受空字典 `{}`
   - 单文档：使用 `None`
   - 批量：使用占位符 `{"_placeholder": "true"}`

2. **NumPy 数组处理**：
   ```python
   # ❌ 错误
   embedding = results["embeddings"][0] if results["embeddings"] else None

   # ✅ 正确
   embedding = None
   if results.get("embeddings") is not None and len(results["embeddings"]) > 0:
       embedding = results["embeddings"][0]
   ```

3. **批量操作**：
   - 使用 `add_documents()` 批量插入
   - 配置 `batch_size=100` 平衡性能
   - 返回 `BatchInsertResult` 跟踪成功/失败

### Jira 数据结构要点 (Task 1.3)

- **JiraIssue 核心字段**：
  - `summary`: 标题（必需）
  - `description`: 详细描述（可选）
  - `comments`: 评论列表（关联数据）
  - `labels`, `components`: 标签和组件
  - `status`, `priority`, `issue_type`: 分类信息

- **分页查询**：
  ```python
  page = client.fetch_issues(
      project_key="PROJ",
      start_at=0,
      max_results=100
  )
  ```

### Embedding 模型 (Task 1.1-1.2)

- **默认模型**: `bge-large-zh` (中文大模型)
- **维度**: 1024 维
- **使用方式**:
  ```python
  manager = get_llm_manager()
  embedding = manager.create_embedding()  # 自动缓存
  response = await embedding.embed(text)
  ```

### RAG 文档索引 (Task 1.5)

1. **文本分块策略**:
   - 固定长度分块：800 字符，150 重叠
   - 智能边界调整（优先在句子结束处分割）
   - Chunk ID 格式：`parent_id_chunk_index`

2. **内容组装格式**:
   ```markdown
   # Issue 标题
   ## 描述
   描述内容...
   ## 评论
   ### 评论 1 - 作者
   评论内容...
   ```

3. **批量处理**:
   - Jira Issues: 50 个/批次
   - Embedding: 批量生成
   - ChromaDB 插入: 100 个/批次

4. **相似度计算**:
   ```python
   # 距离转分数（0-1，越大越相似）
   score = 1.0 / (1.0 + distance)
   ```

5. **模块结构**:
   - `TextChunker`: 文本分块器
   - `DocumentIndexer`: 文档索引器
   - `VectorRetriever`: 向量检索器
   - 12 个单元测试，覆盖率 95%+

### Web UI 对话界面 (Task 1.7) ⭐ 新增

#### FastAPI 后端架构

1. **数据模型设计** (`src/api/schemas/`):
   ```python
   # 核心模型（使用 Pydantic v2 ConfigDict）
   - ChatMessage: 单条消息（role, content, timestamp）
   - ChatRequest: 对话请求（message, session_id, enable_rag, rag_top_k）
   - ChatResponse: 对话响应（session_id, message, retrieved_contexts）
   - RetrievedContext: RAG 检索结果（chunk_id, content, score, source）
   - ChatHistory: 会话历史（messages列表）
   ```

2. **会话管理策略** (`SessionManager`):
   - **存储**: 内存缓存（快速访问）+ JSON 文件持久化（防丢失）
   - **TTL**: 30分钟无活动自动过期
   - **容量**: 最多保留 100 条消息（自动裁剪）
   - **文件路径**: `./data/chat_history/{session_id}.json`

3. **对话服务流程** (`ChatService.chat()`):
   ```
   1. 创建/获取会话 (UUID)
   2. RAG 检索（如果启用）
      → VectorRetriever.retrieve(query, top_k)
      → 构建增强提示词
   3. 加载历史消息（最近 20 条）
   4. 构建对话上下文（System + History + Current）
   5. LLM 生成
   6. 保存对话历史
   7. 返回响应（含 retrieved_contexts）
   ```

4. **API 端点（7/7 全部实现）**:
   ```
   ✅ POST /api/v1/chat/message        # 非流式对话
   ✅ POST /api/v1/chat/stream         # 流式对话（SSE）✨ 新增
   ✅ GET  /api/v1/chat/history/{id}   # 获取历史
   ✅ DELETE /api/v1/chat/history/{id} # 清空历史
   ✅ GET  /api/v1/models/list         # 模型列表
   ✅ GET  /api/v1/models/status       # 模型状态
   ✅ GET  /api/v1/health              # 健康检查
   ```

4.1. **流式响应实现** (`ChatService.chat_stream()`): ✨ 新增
   - 事件流格式：
     - `start`: 开始生成（含 session_id）
     - `context`: RAG 检索结果（可选）
     - `token`: 生成的文本片段（实时推送）
     - `end`: 生成结束（含统计信息）
     - `error`: 错误信息
   - SSE 完整实现（sse-starlette）
   - 异步流式生成（AsyncIterator）

5. **RAG 提示词模板**:
   ```python
   prompt = f"""请基于以下相关文档回答用户问题。

   相关文档：
   [文档 1 - PROJ-123]
   文档内容...

   用户问题：{query}

   请提供准确、简洁的回答，并在回答末尾注明引用的文档来源。"""
   ```

#### Gradio 前端架构 ✨ 新增

1. **API 客户端** (`src/ui/utils/api_client.py`):
   ```python
   class ChatAPIClient:
       - chat(): 非流式对话
       - chat_stream(): 流式对话（AsyncIterator）
       - get_history(), clear_history(): 历史管理
       - get_models(): 获取模型列表
       - health_check(): 健康检查
   ```
   - 完整的 SSE 事件流解析
   - 错误处理和重连机制
   - httpx 异步客户端

2. **对话页面** (`src/ui/pages/chat_page.py`):
   - **UI 组件**:
     - Chatbot: 对话显示区域
     - Textbox: 用户输入框
     - Button: 发送按钮、清空按钮
     - Dropdown: 模型选择器
     - Checkbox: RAG 开关
     - Slider: RAG 参数（top_k, temperature）
     - Examples: 示例问题
   - **事件处理**:
     - `user_input_handler`: 添加用户消息到历史
     - `bot_response_handler`: 流式响应实时更新（打字机效果）
     - `clear_history_handler`: 清空历史
   - **状态管理**: gr.State 保存 session_id

3. **主程序入口** (`src/main.py`):
   ```python
   def main():
       # threading 并发启动
       fastapi_thread = Thread(target=run_fastapi, daemon=True)
       fastapi_thread.start()

       # 主线程运行 Gradio（阻塞）
       run_gradio()
   ```

#### 关键技术决策

1. **Gradio + FastAPI 分离架构**:
   - FastAPI: 后端 API（端口 7860）
   - Gradio: 前端 UI（端口 7861）
   - 通信: HTTP POST/GET + SSE 流式

2. **流式响应方案**: Server-Sent Events (SSE)
   - 比 WebSocket 更简单
   - 浏览器自动重连
   - Gradio 原生支持

3. **会话管理**: UUID + 无认证（MVP）
   - 首次对话生成 session_id
   - 前端保存在 gr.State
   - 未来扩展: JWT + 用户认证

---

## 🔍 调试和验证 | Debug & Verification

### 快速测试命令

```bash
# 1. 启动 Web UI（一键启动）⭐ 最新
python src/main.py
# → FastAPI: http://localhost:7860/docs
# → Gradio: http://localhost:7861

# 2. 测试 FastAPI 后端导入
python -c "from src.api import app; print('✓ FastAPI app OK')"

# 3. 测试 Gradio 前端导入 ⭐ 新增
python -c "from src.ui.app import create_app; print('✓ Gradio app OK')"

# 4. 测试 SessionManager
python -c "
from src.api.services import get_session_manager
import asyncio
async def test():
    manager = get_session_manager()
    print(f'✓ SessionManager OK: {manager.storage_dir}')
asyncio.run(test())
"

# 5. 测试 ChatService
python -c "from src.api.services import get_chat_service; print('✓ ChatService OK')"

# 6. 测试流式响应（需先启动 FastAPI）⭐ 新增
python tests/manual/test_streaming.py

# 7. 运行 RAG 模块单元测试
pytest tests/unit/test_rag/test_chunker.py -v
# 12 passed in 2.34s

# 5. 运行 RAG 使用示例
python examples/rag_example.py

# 6. 运行所有测试
pytest tests/unit/ -v
```

### 健康检查

```bash
# 检查 Ollama 服务
curl http://localhost:11434/api/tags

# 检查 Jira 连接
python -c "from src.integrations.jira import get_jira_client; import asyncio; client = get_jira_client(); print(asyncio.run(client.health_check()))"

# 检查 ChromaDB
python -c "from src.core.vectordb import get_chroma_client; print(get_chroma_client().health_check())"
```

---

## 📚 文档资源 | Documentation

### 已完成文档

1. **`docs/SPRINT1_TASK1.1_SUMMARY.md`**
   LLM 和 Ollama 集成总结

2. **`docs/SPRINT1_TASK1.6_CHROMADB.md`** (1,435 行)
   ChromaDB 集成详细文档，包含：
   - 完整实现说明
   - 3 个问题和解决方案
   - 8 个使用示例
   - 性能优化建议

3. **`docs/SPRINT1_TASK1.5_RAG_INDEXING.md`** (620 行) ⭐ 新增
   RAG 基础文档索引实现总结，包含：
   - 完整架构设计和数据流
   - 核心组件实现详解
   - 12 个单元测试说明
   - 使用示例和配置参数
   - 性能优化建议

4. **`docs/OLLAMA_DOCKER_SETUP.md`**
   Ollama Docker 部署指南

5. **`docs/TEST_REPORT_*.md`**
   各模块测试报告

### 代码示例

- **`examples/rag_example.py`** ⭐ 新增
  RAG 模块完整使用示例（索引 + 检索）

### 待创建文档

- `docs/RAG_ARCHITECTURE.md` - RAG 系统架构详解（可选）
- `docs/SPRINT1_SUMMARY.md` - Sprint 1 总结报告

---

## 🛠️ 开发环境 | Development Environment

### 关键配置文件

- **`.env`**: 环境变量（Jira/Confluence 凭据、Ollama 配置）
- **`src/config.py`**: 应用配置（使用 pydantic-settings）
- **`pyproject.toml`**: 项目依赖和工具配置

### 已安装的关键依赖

```
chromadb>=0.4.22      # 向量数据库
jira>=3.5.0           # Jira Python SDK
atlassian-python-api  # Confluence Python SDK
pydantic>=2.0.0       # 数据验证
tenacity>=8.0.0       # 重试机制
httpx                 # 异步 HTTP 客户端
```

### 需要添加的依赖 (Task 1.5)

```bash
# 可能需要的分块和文本处理库
pip install tiktoken      # Token 计数（OpenAI）
pip install langchain     # 可选：现成的 Chunker
```

---

## 🎓 经验教训 | Lessons Learned

### ChromaDB 集成 (Task 1.6)

1. **NumPy 数组不能直接布尔判断**
   使用 `is not None` 和 `len()` 显式检查

2. **空元数据被拒绝**
   批量操作时使用占位符保持一致性

3. **测试隔离很重要**
   使用临时目录和 fixture 确保测试独立性

### RAG 文档索引 (Task 1.5)

1. **文本分块边界调整**
   - 优先在句子边界分割（句号、问号、感叹号）
   - 次优在标点处分割（逗号、分号、冒号）
   - 避免截断重要信息

2. **Chunk ID 设计**
   - 格式：`parent_id_chunk_index`
   - 保证唯一性和可追溯性
   - 便于后续的块管理

3. **批量操作优化**
   - Jira Issues: 50 个/批次
   - Embedding 生成: 批量调用
   - ChromaDB 插入: 100 个/批次
   - 显著减少 API 调用次数

4. **元数据完整保留**
   - 从 Issue 到 Chunk 再到检索结果
   - 保留所有关键信息（项目、类型、状态等）
   - 支持后续的过滤和溯源

### 代码质量管理 ⭐ 新增

1. **Pydantic v2 迁移**
   - 使用 `ConfigDict` 替代 `class Config`
   - 避免弃用警告
   - 保持代码现代化

2. **编译检查流程**
   - 定期运行 `python -m py_compile` 检查语法
   - 测试核心模块导入
   - 运行单元测试验证功能

3. **代码规范**
   - 使用 logging 而非 loguru（保持一致）
   - 遵循项目现有模式
   - 保持代码可读性和可维护性

### 项目开发模式

1. **遵循现有模式**：
   - 每个模块包含 `models.py`, `exceptions.py`, `client.py`
   - 使用 Pydantic 进行数据验证
   - 自定义异常层次结构
   - 全局单例 + 上下文管理器

2. **测试驱动**：
   - 单元测试 + 集成测试
   - Mock 外部依赖
   - 使用 pytest fixtures
   - 目标覆盖率 > 90%

3. **文档先行**：
   - 详细记录问题和解决方案
   - 提供完整的使用示例
   - 创建 docs/ 下的总结文档

---

## 📅 时间规划 | Timeline

**Sprint 1 截止日期**: 2026-01-16 (还剩 4 天)

| 日期 | 计划任务 | 实际进度 |
|------|---------|---------|
| 2026-01-12 | Task 1.5 实现 | ✅ 完成：RAG 模块（1,181 行），12 个测试通过 |
| 2026-01-13 | Task 1.7 Web UI (Day 1) | 对话界面框架和基础组件 |
| 2026-01-14 | Task 1.7 Web UI (Day 2) | 集成 RAG 检索和测试 |
| 2026-01-15 | Sprint 1 收尾 (Day 3) | 整体测试、文档和验收 |
| 2026-01-16 | Sprint 1 总结 (Day 4) | Sprint 回顾和计划 Sprint 2 |

---

## 🚀 快速恢复工作 | Quick Resume

### 1️⃣ 第一步：查看最新状态

```bash
# 进入项目目录
cd /Users/macbook/ai-project/KT-BOT

# 查看 git 状态
git status
git log --oneline -5

# 查看 Sprint 进度
cat SPRINTS.md | grep -A 20 "Sprint 1"
```

### 2️⃣ 第二步：确认开发环境

```bash
# 检查 Python 环境
python --version

# 检查依赖安装
pip list | grep -E "chromadb|jira|atlassian|pydantic"

# 检查 Ollama 服务
curl http://localhost:11434/api/tags
```

### 3️⃣ 第三步：测试 RAG 模块

**Task 1.5 已完成** ✅

验证 RAG 模块是否正常工作：

```bash
# 1. 运行单元测试
pytest tests/unit/test_rag/test_chunker.py -v

# 2. 测试模块导入
python -c "from src.core.rag import *; print('RAG module OK')"

# 3. 查看代码统计
find src/core/rag -name "*.py" -exec wc -l {} + | tail -1
```

### 4️⃣ 第四步：继续 Task 1.7

**当前任务**：Web UI 对话界面（5 故事点，75% 完成）

**✅ 已完成**：
- FastAPI 后端 API（数据模型 + 会话管理 + 对话服务）
- 非流式对话功能（含 RAG 集成）
- 历史记录管理

**⏳ 待完成**：
```
继续 Task 1.7 - 还剩 25% 工作量
需要实现：
1. Phase 1.4: 流式响应（SSE）- 2-3小时
2. Phase 2: Gradio 前端 UI - 1天
   - 2.1: 基础布局（Chatbot + Textbox + Button）
   - 2.2: API 客户端（httpx 调用 FastAPI）
   - 2.3: 事件处理（流式响应实时更新）
   - 2.4: UI 优化（示例问题、来源引用、样式）
3. Phase 3: 集成测试（端到端验证）- 半天
4. Phase 4: 单元测试和文档 - 半天

快速恢复命令：
# 测试当前后端
python -c "from src.api import app; print('✓ FastAPI ready')"

# 查看实现计划
cat ~/.claude/plans/fuzzy-wondering-sketch.md

# 查看待办事项
# 已完成: Phase 1.1, 1.2, 1.3
# 进行中: Phase 1.4 (流式响应)
```

---

## 📞 联系和协作 | Contact & Collaboration

**开发者**: Claude Sonnet 4.5
**项目**: KT-BOT - Enterprise Knowledge Bot
**仓库**: `/Users/macbook/ai-project/KT-BOT`

---

**书签创建时间**: 2026-01-12
**最近更新**: 2026-01-14 (Task 1.7 FastAPI 后端完成 75%)
**下次更新**: 完成 Phase 1.4 流式响应或 Phase 2 Gradio UI 后更新
