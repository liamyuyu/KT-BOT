# KT-BOT 开发书签 / Development Bookmarks

> **最后更新**: 2026-01-28
> **当前 Sprint**: Sprint 5
> **当前版本**: v0.3.0-dev

---

## 📍 当前进度 / Current Progress

### Sprint 5 - 对话历史管理和文档上传

**总体进度**: 10/34 故事点完成 (29.4%)

| Story | 状态 | 故事点 | 完成度 | 备注 |
|-------|------|--------|--------|------|
| Story 5.1: 对话历史管理 | ✅ 已完成 | 10点 | 100% | 2026-01-28 完成 |
| Story 5.2: 文档上传增强 | ⏳ 待开始 | 8点 | 0% | 下一个任务 |
| Story 5.3: 引用溯源优化 | ⏳ 待开始 | 8点 | 0% | |
| Story 5.4: Docker 部署优化 | ⏳ 待开始 | 5点 | 0% | |
| Story 5.5: 性能监控面板 | ⏳ 待开始 | 3点 | 0% | |

---

## 🎯 当前任务 / Current Task

**Story 5.1: 对话历史管理** - ✅ 已完成

### 完成情况

- ✅ Phase 1: 数据模型和持久化 (100%)
- ✅ Phase 2: 对话管理服务 (100%)
- ✅ Phase 3: API 端点 (100%)
- ✅ Phase 4: UI 界面 (100%)
- ✅ Phase 5: 测试 (100%)

### 关键文件

**已创建文件** (24个):
```
src/storage/database/models.py                              # 数据模型 (Conversation, Message)
src/storage/database/migrations/versions/799cb8d29ff0_*.py  # Alembic 迁移
src/storage/database/repository/conversation_repo.py        # 数据访问层
src/services/conversation/models.py                         # Pydantic 模型
src/services/conversation/title_generator.py                # 标题生成器
src/services/conversation/exporters.py                      # 导出器
src/services/conversation/manager.py                        # 业务逻辑
src/api/routes/conversations.py                             # API 端点
src/ui/utils/api_client.py                                  # API 客户端 (扩展)
src/ui/pages/history_page.py                                # 对话历史页面
tests/unit/test_conversation/test_repository.py             # 单元测试
tests/unit/test_conversation/test_manager.py                # 单元测试
tests/unit/test_conversation/test_title_generator.py        # 单元测试
tests/integration/test_conversation_api.py                  # 集成测试
tests/e2e/test_conversation_flow.py                         # 端到端测试
docs/SPRINT5_STORY5.1_PHASE1_SUMMARY.md                     # Phase 1 文档
docs/SPRINT5_STORY5.1_PHASE2_SUMMARY.md                     # Phase 2 文档
docs/SPRINT5_STORY5.1_PHASE3_SUMMARY.md                     # Phase 3 文档
docs/SPRINT5_STORY5.1_PHASE4_SUMMARY.md                     # Phase 4 文档
docs/SPRINT5_STORY5.1_PHASE5_SUMMARY.md                     # Phase 5 文档
docs/SPRINT5_STORY5.1_COMPLETE_SUMMARY.md                   # 完整总结
```

### 代码统计
- 生产代码: ~2,759 行
- 测试代码: ~2,210 行
- 文档: ~3,500 行
- **总计**: ~8,469 行

### 测试覆盖
- 单元测试: 59 个（~95% 覆盖率）
- 集成测试: 20 个（~90% 覆盖率）
- 端到端测试: 3 个场景
- **总计**: 82 个测试，100% 通过

---

## 📝 下一步计划 / Next Steps

### Story 5.2: 文档上传增强 (8点)

**目标**: 完善文档上传功能，支持多格式、批量上传、进度显示

**实施计划**:
1. Phase 1: 文档解析器增强 (2天)
   - 完善 PDF 解析（文本、表格）
   - 完善 DOCX 解析
   - 实现 Markdown、HTML 解析
   - 文件验证器

2. Phase 2: 上传管理器 (2天)
   - UploadManager 实现
   - 异步文档处理
   - 进度跟踪（SSE）
   - 批量上传支持

3. Phase 3: API 端点 (1天)
   - 上传 API 实现
   - 批量上传 API
   - 状态查询 API

4. Phase 4: UI 增强 (2天)
   - 拖拽上传
   - 实时进度条
   - 多文件选择
   - 上传历史

5. Phase 5: 测试 (1天)
   - 各格式文档测试
   - 大文件测试
   - 并发上传测试

**预计开始时间**: 2026-01-29

---

## 🗂️ 项目结构书签 / Project Structure Bookmarks

### 核心模块 / Core Modules

**LLM 管理** (`src/core/llm/`):
- `manager.py` - LLM 管理器（模型加载、切换、健康检查）
- `ollama.py` - Ollama 集成
- `config.py` - 模型配置管理

**RAG 引擎** (`src/core/rag/`):
- `retriever/vector.py` - 向量检索器
- `retriever/bm25.py` - BM25 检索器
- `retriever/hybrid.py` - 混合检索器
- `reranker/cross_encoder.py` - 重排序器
- `indexer.py` - 文档索引器
- `chunker.py` - 文本分块器

**对话历史** (`src/services/conversation/`):
- `manager.py` - 对话管理器
- `title_generator.py` - 标题生成器
- `exporters.py` - 导出器
- `models.py` - 数据模型

**向量数据库** (`src/core/vectordb/`):
- `chroma_client.py` - ChromaDB 客户端

**集成模块** (`src/integrations/`):
- `jira/client.py` - Jira API 客户端
- `confluence/client.py` - Confluence API 客户端

**同步调度** (`src/sync/`):
- `scheduler/scheduler.py` - 同步调度器
- `scheduler/task.py` - 任务执行器
- `scheduler/repository.py` - 数据持久化

### API 层 / API Layer

**API 端点** (`src/api/routes/`):
- `chat.py` - 对话接口（7个端点）
- `documents.py` - 文档管理（7个端点）
- `search.py` - 搜索接口（3个端点）
- `sync.py` - 同步管理（13个端点）
- `conversations.py` - 对话历史（12个端点）✨ 新增
- `models.py` - 模型管理（4个端点）
- `health.py` - 健康检查（2个端点）

**服务层** (`src/api/services/`):
- `chat_service.py` - 对话服务
- `document_service.py` - 文档服务

### UI 层 / UI Layer

**UI 页面** (`src/ui/pages/`):
- `chat_page.py` - 对话页面
- `document_page.py` - 文档管理页面
- `search_page.py` - 搜索页面
- `sync_page.py` - 同步管理页面
- `settings_page.py` - 设置页面
- `history_page.py` - 对话历史页面 ✨ 新增

**工具类** (`src/ui/utils/`):
- `api_client.py` - API 客户端（扩展了对话历史方法）

### 数据库 / Database

**模型** (`src/storage/database/models.py`):
- `Conversation` - 对话会话模型 ✨ 新增
- `Message` - 对话消息模型 ✨ 新增

**迁移** (`src/storage/database/migrations/versions/`):
- `001_create_sync_tables.py` - 同步表
- `799cb8d29ff0_*.py` - 对话表 ✨ 新增

**Repository** (`src/storage/database/repository/`):
- `conversation_repo.py` - 对话数据访问层 ✨ 新增

---

## 📚 文档书签 / Documentation Bookmarks

### 项目文档

- [README.md](./README.md) - 项目介绍和快速开始
- [Requirements.md](./Requirements.md) - 需求文档
- [SPRINTS.md](./SPRINTS.md) - Sprint 规划
- [CHANGELOG.md](./CHANGELOG.md) - 更新日志
- [BOOKMARKS.md](./BOOKMARKS.md) - 开发书签（本文档）

### Sprint 5 文档

**Story 5.1 对话历史管理**:
- [docs/SPRINT5_STORY5.1_PHASE1_SUMMARY.md](./docs/SPRINT5_STORY5.1_PHASE1_SUMMARY.md) - Phase 1 总结
- [docs/SPRINT5_STORY5.1_PHASE2_SUMMARY.md](./docs/SPRINT5_STORY5.1_PHASE2_SUMMARY.md) - Phase 2 总结
- [docs/SPRINT5_STORY5.1_PHASE3_SUMMARY.md](./docs/SPRINT5_STORY5.1_PHASE3_SUMMARY.md) - Phase 3 总结
- [docs/SPRINT5_STORY5.1_PHASE4_SUMMARY.md](./docs/SPRINT5_STORY5.1_PHASE4_SUMMARY.md) - Phase 4 总结
- [docs/SPRINT5_STORY5.1_PHASE5_SUMMARY.md](./docs/SPRINT5_STORY5.1_PHASE5_SUMMARY.md) - Phase 5 总结
- [docs/SPRINT5_STORY5.1_COMPLETE_SUMMARY.md](./docs/SPRINT5_STORY5.1_COMPLETE_SUMMARY.md) - 完整总结

**Sprint 5 规划**:
- [docs/SPRINT5_PLAN.md](./docs/SPRINT5_PLAN.md) - Sprint 5 实施计划

### Sprint 4 文档

- [docs/STORY_4.5_COMPLETION_SUMMARY.md](./docs/STORY_4.5_COMPLETION_SUMMARY.md) - 搜索功能
- [docs/STORY_4.6_COMPLETION_SUMMARY.md](./docs/STORY_4.6_COMPLETION_SUMMARY.md) - 模型切换
- [docs/STORY_4.7_COMPLETION_SUMMARY.md](./docs/STORY_4.7_COMPLETION_SUMMARY.md) - 同步状态
- [docs/SPRINT4_COMPLETION_SUMMARY.md](./docs/SPRINT4_COMPLETION_SUMMARY.md) - Sprint 4 总结

### API 文档

- FastAPI Swagger UI: http://localhost:7860/docs
- ReDoc: http://localhost:7860/redoc

---

## 🔧 配置文件书签 / Configuration Bookmarks

### 核心配置

- `.env` - 环境变量配置
- `config/models.yaml` - 模型配置
- `config/logging.yaml` - 日志配置
- `config/retrieval.yaml` - 检索配置

### Docker 配置

- `Dockerfile` - Docker 镜像构建
- `docker-compose.yml` - Docker Compose 配置
- `.dockerignore` - Docker 忽略文件

### 数据库配置

- `alembic.ini` - Alembic 配置
- `src/storage/database/migrations/` - 数据库迁移

---

## 🧪 测试书签 / Testing Bookmarks

### 测试目录结构

```
tests/
├── unit/                          # 单元测试
│   ├── test_conversation/         # 对话历史测试 ✨ 新增
│   │   ├── test_repository.py     # Repository 测试（27个）
│   │   ├── test_manager.py        # Manager 测试（15个）
│   │   └── test_title_generator.py # 标题生成器测试（17个）
│   ├── api/                       # API 测试
│   │   ├── test_models_api.py     # 模型 API 测试
│   │   ├── test_search_api.py     # 搜索 API 测试
│   │   └── test_sync_api.py       # 同步 API 测试
│   ├── services/                  # 服务测试
│   │   └── test_document_search.py # 搜索服务测试
│   └── sync/                      # 同步测试
├── integration/                   # 集成测试
│   ├── test_conversation_api.py   # 对话历史 API 测试 ✨ 新增（20个）
│   └── test_sync_end_to_end.py    # 同步端到端测试
└── e2e/                          # 端到端测试
    ├── test_conversation_flow.py  # 对话流程测试 ✨ 新增（3个场景）
    └── test_rag_simple.py         # RAG 测试
```

### 测试命令

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行对话历史测试
pytest tests/unit/test_conversation/ -v

# 运行集成测试
pytest tests/integration/test_conversation_api.py -v

# 运行端到端测试
pytest tests/e2e/test_conversation_flow.py -v

# 运行测试并生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 测试覆盖率

- 整体覆盖率: ~55%
- 对话历史模块: ~95%
- 搜索模块: ~85%
- 同步模块: ~82%

---

## 🚀 快速命令 / Quick Commands

### 开发环境

```bash
# 启动开发服务器
python src/main.py

# 启动 FastAPI（仅后端）
uvicorn src.api.main:app --reload --port 7860

# 启动 Gradio（仅前端）
python src/ui/app.py

# 数据库迁移
alembic upgrade head

# 创建新迁移
alembic revision -m "description"
```

### 代码质量

```bash
# 运行测试
pytest

# 代码格式化
black src/ tests/

# 类型检查
mypy src/

# Lint 检查
ruff check src/
```

### Docker

```bash
# 构建镜像
docker build -t kt-bot:latest .

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止所有服务
docker-compose down
```

---

## 📊 项目统计 / Project Statistics

### 代码统计（截至 2026-01-28）

| 模块 | 文件数 | 代码行数 | 测试行数 | 覆盖率 |
|------|--------|----------|----------|--------|
| LLM 管理 | 10 | ~1,200 | ~443 | 85% |
| RAG 引擎 | 15 | ~3,500 | ~1,500 | 90% |
| 集成模块 | 8 | ~2,000 | ~1,400 | 95% |
| 同步调度 | 10 | ~2,000 | ~3,400 | 82% |
| API 层 | 12 | ~2,800 | ~800 | 75% |
| UI 层 | 8 | ~2,500 | ~250 | 60% |
| 对话历史 | 10 | ~2,759 | ~2,210 | 95% |
| **总计** | **73** | **~16,759** | **~10,003** | **~72%** |

### Sprint 进度统计

| Sprint | 故事点 | 完成状态 | 主要功能 |
|--------|--------|----------|----------|
| Sprint 1 | 20点 | ✅ 100% | LLM 集成、Jira/Confluence、基础 RAG |
| Sprint 2 | 29点 | ✅ 100% | 混合检索、重排序、文档管理 |
| Sprint 3 | 42点 | ✅ 100% | 模型管理、引用溯源、文档上传 |
| Sprint 4 | 35点 | ✅ 100% | 同步调度、搜索功能、模型切换 |
| Sprint 5 | 34点 | 🔄 29.4% | 对话历史、文档上传增强 |
| **总计** | **160点** | **🔄 89.4%** | |

---

## 🎯 里程碑 / Milestones

### 已完成的里程碑

- ✅ **v0.1.0** (2025-12-30): MVP 发布
- ✅ **Sprint 1** (2026-01-16): 基础架构完成
- ✅ **Sprint 2** (2026-01-20): RAG 增强完成
- ✅ **Sprint 3** (2026-01-21): 模型管理完成
- ✅ **Sprint 4** (2026-01-28): 数据同步和搜索完成
- ✅ **Story 5.1** (2026-01-28): 对话历史管理完成

### 即将到来的里程碑

- ⏳ **Story 5.2** (预计 2026-02-05): 文档上传增强
- ⏳ **Story 5.3** (预计 2026-02-12): 引用溯源优化
- ⏳ **Sprint 5** (预计 2026-02-28): 对话历史和文档上传完成
- ⏳ **v0.3.0** (预计 2026-02-28): Sprint 5 发布

---

## 📌 重要链接 / Important Links

### 内部链接

- 项目仓库: `/Users/macbook/ai-project/KT-BOT/`
- 数据目录: `./data/`
- 日志目录: `./logs/`
- 配置目录: `./config/`

### 外部链接

- Ollama 文档: https://ollama.ai/
- ChromaDB 文档: https://docs.trychroma.com/
- FastAPI 文档: https://fastapi.tiangolo.com/
- Gradio 文档: https://www.gradio.app/docs/

### 依赖库

- httpx: https://www.python-httpx.org/
- SQLAlchemy: https://www.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- jieba: https://github.com/fxsjy/jieba
- sentence-transformers: https://www.sbert.net/

---

## 🔖 个人笔记 / Personal Notes

### 开发技巧

1. **数据库迁移**: 修改模型后记得创建迁移 `alembic revision -m "xxx"`
2. **测试先行**: 先写测试用例，再实现功能（TDD）
3. **API 文档**: 修改 API 后访问 `/docs` 验证文档生成
4. **异步处理**: 耗时操作使用异步，避免阻塞主线程
5. **错误处理**: 使用自定义异常类，统一错误响应格式

### 常见问题

1. **端口占用**: `lsof -ti:7860 | xargs kill -9`
2. **数据库锁**: 重启应用，清理僵死连接
3. **Ollama 连接**: 确保 Ollama 服务运行 `ollama list`
4. **依赖冲突**: 使用虚拟环境隔离依赖

### 待办事项

- [ ] 完成 Story 5.2: 文档上传增强
- [ ] 完成 Story 5.3: 引用溯源优化
- [ ] 完成 Story 5.4: Docker 部署优化
- [ ] 完成 Story 5.5: 性能监控面板
- [ ] 提升整体测试覆盖率到 80%
- [ ] 编写用户使用文档
- [ ] 性能优化和压力测试

---

**文档维护**: Claude Sonnet 4.5
**最后更新**: 2026-01-28
**下次更新**: Story 5.2 完成后
