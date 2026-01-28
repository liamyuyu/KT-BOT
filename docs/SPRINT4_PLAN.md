# Sprint 4 实施计划

> **Sprint 周期**: 2026-01-27 ~ 2026-02-27 (31天)
> **总故事点数**: 31 点
> **预计完成率**: 100%
> **Sprint 目标**: 数据同步调度、检索过滤、UI 增强

---

## 📋 Sprint 4 用户故事清单

| 序号 | 用户故事 | 故事点 | 优先级 | 预估工作量 | 依赖关系 |
|------|---------|--------|--------|-----------|---------|
| 1 | Story 2.3: 数据同步调度器 | 5点 | P0 | 3-4天 | 无 |
| 2 | Story 3.7: 检索结果过滤 | 5点 | P1 | 2-3天 | 无 |
| 3 | Story 4.5: 搜索功能 | 8点 | P1 | 4-5天 | Story 2.3 部分依赖 |
| 4 | Story 4.6: 模型切换 UI | 5点 | P2 | 2-3天 | 无 |
| 5 | Story 4.7: 同步状态显示 | 8点 | P1 | 3-4天 | Story 2.3 |

**总计**: 31 故事点，预估 14-19 工作日

---

## 🎯 Story 2.3: 数据同步调度器 (5点) - P0 优先级

### 用户故事
**作为** 系统管理员
**我希望** 系统能够自动同步 Jira 和 Confluence 数据
**以便** 确保知识库始终保持最新状态，无需手动触发同步

### 验收标准
- [ ] 支持定时自动同步（可配置时间间隔）
- [ ] 支持增量同步（只同步变更的数据）
- [ ] 支持全量同步（可手动触发）
- [ ] 同步任务可启动/停止/重启
- [ ] 同步失败自动重试机制（最多3次）
- [ ] 同步历史记录可查询
- [ ] 同步错误日志可查看

### 技术设计

#### 1. 调度器架构
```
SyncScheduler（调度器）
├── APScheduler（定时任务框架）
├── SyncTask（同步任务）
│   ├── JiraSyncTask
│   └── ConfluenceSyncTask
├── SyncHistory（同步历史）
└── SyncConfig（同步配置）
```

#### 2. 核心组件

**文件结构**:
```
src/services/sync/
├── __init__.py
├── scheduler.py          # 调度器主逻辑（SyncScheduler）
├── tasks.py              # 同步任务实现（JiraSyncTask, ConfluenceSyncTask）
├── models.py             # 数据模型（SyncTask, SyncHistory, SyncConfig）
├── repository.py         # 数据访问层（SyncHistoryRepo）
└── exceptions.py         # 自定义异常

src/api/routes/
└── sync.py               # 同步相关 API 端点

config/
└── sync_config.yaml      # 同步配置文件
```

**数据模型**:
```python
# SyncConfig
class SyncConfig(BaseModel):
    source: str  # jira | confluence
    enabled: bool
    schedule_type: str  # cron | interval
    schedule_value: str  # "0 */6 * * *" | "3600"
    incremental: bool
    batch_size: int
    retry_attempts: int
    retry_delay: int

# SyncTask
class SyncTask(BaseModel):
    task_id: str
    source: str
    status: str  # pending | running | completed | failed
    start_time: datetime
    end_time: Optional[datetime]
    total_items: int
    synced_items: int
    failed_items: int
    error_message: Optional[str]

# SyncHistory
class SyncHistory(BaseModel):
    id: str
    task_id: str
    source: str
    sync_type: str  # full | incremental
    status: str
    items_synced: int
    duration_seconds: int
    created_at: datetime
```

#### 3. API 端点设计

```python
# 同步配置管理
GET    /api/v1/sync/config                  # 获取所有配置
GET    /api/v1/sync/config/{source}         # 获取指定源配置
PUT    /api/v1/sync/config/{source}         # 更新配置
POST   /api/v1/sync/config/{source}/enable  # 启用自动同步
POST   /api/v1/sync/config/{source}/disable # 禁用自动同步

# 手动触发同步
POST   /api/v1/sync/trigger                 # 触发同步（支持 jira/confluence/all）
POST   /api/v1/sync/trigger/full            # 触发全量同步

# 同步状态查询
GET    /api/v1/sync/tasks                   # 获取所有任务
GET    /api/v1/sync/tasks/{task_id}         # 获取任务详情
GET    /api/v1/sync/tasks/running           # 获取运行中的任务
DELETE /api/v1/sync/tasks/{task_id}         # 取消任务

# 同步历史记录
GET    /api/v1/sync/history                 # 获取历史记录（支持分页和过滤）
GET    /api/v1/sync/history/{id}            # 获取历史详情
GET    /api/v1/sync/stats                   # 获取同步统计信息
```

#### 4. 实现步骤

**Phase 1: 调度器核心（2天）**
- [ ] 创建 SyncScheduler 类
  - APScheduler 集成
  - 任务调度逻辑
  - 任务状态管理
- [ ] 创建 SyncTask 基类
  - 增量同步逻辑（基于 updated_at）
  - 全量同步逻辑
  - 重试机制
- [ ] 创建配置加载器
  - 从 YAML 加载配置
  - 配置热重载
- [ ] 单元测试（调度器核心）

**Phase 2: Jira/Confluence 同步任务（1.5天）**
- [ ] 实现 JiraSyncTask
  - 增量同步：`updated >= last_sync_time`
  - 批量处理（50个/批次）
  - 索引更新
- [ ] 实现 ConfluenceSyncTask
  - 增量同步：`lastModified >= last_sync_time`
  - 批量处理
  - 索引更新
- [ ] 单元测试（同步任务）

**Phase 3: 数据持久化（1天）**
- [ ] 创建数据库表（sync_history, sync_config）
- [ ] 实现 SyncHistoryRepo
- [ ] 实现历史记录查询和统计

**Phase 4: API 端点（1天）**
- [ ] 实现所有 12 个 API 端点
- [ ] 集成测试
- [ ] API 文档更新

**Phase 5: 集成测试（0.5天）**
- [ ] 端到端测试（触发同步 → 数据索引 → 检索验证）
- [ ] 性能测试（1000+ Issues 同步）
- [ ] 错误处理测试

#### 5. 配置示例

```yaml
# config/sync_config.yaml
jira:
  enabled: true
  schedule_type: cron
  schedule_value: "0 */6 * * *"  # 每6小时
  incremental: true
  batch_size: 50
  retry_attempts: 3
  retry_delay: 60  # 秒

confluence:
  enabled: true
  schedule_type: interval
  schedule_value: "21600"  # 6小时（秒）
  incremental: true
  batch_size: 30
  retry_attempts: 3
  retry_delay: 60
```

#### 6. 技术依赖
- **APScheduler**: 定时任务框架
- **SQLAlchemy**: 数据库 ORM（历史记录存储）
- **asyncio**: 异步任务执行

#### 7. 风险与挑战
- **并发控制**: 防止多个同步任务同时运行（使用任务锁）
- **大数据量**: Jira 可能有数千个 Issues（分批处理 + 增量同步）
- **API 限流**: Jira/Confluence API 有速率限制（添加 rate limiter）
- **失败恢复**: 同步中断后的恢复机制（保存进度，支持断点续传）

---

## 🎯 Story 3.7: 检索结果过滤 (5点) - P1 优先级

### 用户故事
**作为** 系统用户
**我希望** 能够按来源、时间、类型过滤检索结果
**以便** 快速找到特定范围内的相关文档

### 验收标准
- [ ] 支持按来源过滤（Jira、Confluence、Local）
- [ ] 支持按时间范围过滤（最近1天/7天/30天/自定义）
- [ ] 支持按文档类型过滤（Issue、Page、Document）
- [ ] 支持按优先级过滤（仅 Jira Issue）
- [ ] 支持按状态过滤（仅 Jira Issue）
- [ ] 支持多条件组合过滤
- [ ] 过滤条件可保存和复用

### 技术设计

#### 1. 过滤器架构
```
RetrievalFilter（过滤器）
├── SourceFilter（来源过滤）
├── TimeRangeFilter（时间过滤）
├── TypeFilter（类型过滤）
├── MetadataFilter（元数据过滤）
└── CompositeFilter（组合过滤）
```

#### 2. 核心组件

**文件结构**:
```
src/core/rag/filters/
├── __init__.py
├── base.py              # 过滤器基类（BaseFilter）
├── source_filter.py     # 来源过滤器
├── time_filter.py       # 时间范围过滤器
├── metadata_filter.py   # 元数据过滤器
└── composite_filter.py  # 组合过滤器

src/core/rag/
└── models.py            # 扩展：FilterConfig, FilterResult
```

**数据模型**:
```python
class FilterConfig(BaseModel):
    sources: Optional[List[str]] = None  # ["jira", "confluence"]
    time_range: Optional[TimeRange] = None
    doc_types: Optional[List[str]] = None  # ["issue", "page"]
    metadata: Optional[Dict[str, Any]] = None  # {"priority": "High", "status": "Open"}

class TimeRange(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    preset: Optional[str] = None  # "1d" | "7d" | "30d"
```

#### 3. 实现步骤

**Phase 1: 过滤器基类（1天）**
- [ ] 创建 BaseFilter 抽象类
- [ ] 实现 SourceFilter
- [ ] 实现 TimeRangeFilter
- [ ] 实现 MetadataFilter
- [ ] 单元测试

**Phase 2: 组合过滤（1天）**
- [ ] 实现 CompositeFilter（AND、OR 逻辑）
- [ ] 集成到 VectorRetriever
- [ ] 集成到 HybridRetriever
- [ ] 单元测试

**Phase 3: API 和 UI 集成（1天）**
- [ ] 更新 ChatRequest 模型（添加 filter 字段）
- [ ] 更新 ChatService 应用过滤
- [ ] 更新 Gradio UI（添加过滤面板）
- [ ] 集成测试

#### 4. ChromaDB 元数据过滤

```python
# 使用 ChromaDB 的 where 子句
results = collection.query(
    query_embeddings=[embedding],
    n_results=top_k,
    where={
        "$and": [
            {"source": {"$in": ["jira", "confluence"]}},
            {"created_at": {"$gte": "2026-01-01"}},
            {"priority": "High"}
        ]
    }
)
```

---

## 🎯 Story 4.5: 搜索功能 (8点) - P1 优先级

### 用户故事
**作为** 系统用户
**我希望** 能够全局搜索文档和对话历史
**以便** 快速找到需要的信息

### 验收标准
- [ ] 支持文档全文搜索
- [ ] 支持对话历史搜索
- [ ] 支持搜索建议（自动补全）
- [ ] 搜索结果高亮关键词
- [ ] 搜索结果按相关性排序
- [ ] 搜索历史记录（最近10条）
- [ ] 搜索结果分页显示

### 技术设计

#### 1. 搜索架构
```
SearchService
├── DocumentSearchEngine（文档搜索）
│   ├── BM25 全文搜索
│   └── Vector 语义搜索
├── ChatHistorySearchEngine（对话历史搜索）
└── SearchSuggestionEngine（搜索建议）
```

#### 2. 实现步骤

**Phase 1: 文档搜索（2天）**
- [ ] 创建 DocumentSearchEngine
- [ ] 集成 BM25 和向量搜索
- [ ] 实现关键词高亮
- [ ] 实现分页

**Phase 2: 对话历史搜索（1天）**
- [ ] 创建 ChatHistorySearchEngine
- [ ] 索引对话历史到 ChromaDB
- [ ] 实现搜索和过滤

**Phase 3: 搜索建议（1天）**
- [ ] 基于历史查询的自动补全
- [ ] 基于文档标题的建议

**Phase 4: API 和 UI（2天）**
- [ ] 6 个搜索 API 端点
- [ ] Gradio 搜索界面（新 Tab）
- [ ] 集成测试

---

## 🎯 Story 4.6: 模型切换 UI (5点) - P2 优先级

### 用户故事
**作为** 系统用户
**我希望** 能够在 UI 中切换对话模型和 Embedding 模型
**以便** 根据不同场景选择最合适的模型

### 验收标准
- [ ] UI 显示所有可用模型
- [ ] 支持实时切换对话模型
- [ ] 支持切换 Embedding 模型（需重建索引提示）
- [ ] 显示当前使用的模型
- [ ] 显示模型状态（健康/不可用）
- [ ] 切换后立即生效

### 技术设计

**实现步骤（2-3天）**:
- [ ] Phase 1: 模型管理 API（1天）
  - GET /api/v1/models/list（已有）
  - POST /api/v1/models/switch-llm
  - POST /api/v1/models/switch-embedding
- [ ] Phase 2: Gradio UI（1天）
  - 设置面板添加模型选择器
  - 实时状态更新
- [ ] Phase 3: 测试（0.5天）

---

## 🎯 Story 4.7: 同步状态显示 (8点) - P1 优先级

### 用户故事
**作为** 系统用户
**我希望** 能够查看数据同步的实时状态
**以便** 了解同步进度和处理错误

### 验收标准
- [ ] 实时显示同步进度（进度条）
- [ ] 显示当前同步任务信息
- [ ] 显示同步历史记录
- [ ] 显示同步错误日志
- [ ] 支持手动触发同步
- [ ] 支持取消正在运行的同步
- [ ] 自动刷新状态（WebSocket 或轮询）

### 技术设计

**实现步骤（3-4天）**:
- [ ] Phase 1: 后端推送机制（1.5天）
  - 使用 SSE 实时推送进度
  - 同步任务事件发布
- [ ] Phase 2: Gradio UI（1.5天）
  - 新建"同步状态" Tab
  - 进度条和日志显示
  - 触发同步按钮
- [ ] Phase 3: 测试（1天）

---

## 📅 Sprint 4 时间规划

### 开发顺序（按依赖关系）

**第 1-2 周（2026-01-27 ~ 2026-02-09）**:
- Day 1-4: Story 2.3 数据同步调度器（核心功能）
- Day 5-7: Story 3.7 检索结果过滤
- Day 8-10: Story 4.6 模型切换 UI（独立功能）

**第 3-4 周（2026-02-10 ~ 2026-02-27）**:
- Day 11-15: Story 4.5 搜索功能
- Day 16-19: Story 4.7 同步状态显示（依赖 Story 2.3）
- Day 20-21: 集成测试和 Bug 修复
- Day 22-23: 文档更新
- Day 24: Sprint 回顾

---

## ✅ Sprint 4 验收标准

### 功能验收
- [ ] 数据同步调度器正常运行（定时+手动）
- [ ] 检索结果过滤功能可用
- [ ] 全局搜索功能可用
- [ ] 模型切换 UI 正常工作
- [ ] 同步状态实时显示

### 技术验收
- [ ] 所有单元测试通过（新增 60+ 测试）
- [ ] 集成测试通过
- [ ] 代码覆盖率 > 80%（核心模块）
- [ ] API 文档更新完整
- [ ] 用户指南更新

### 质量验收
- [ ] 无 P0/P1 Bug
- [ ] 性能测试通过（同步 1000+ 文档 < 5分钟）
- [ ] 内存占用 < 1GB
- [ ] API 响应时间 < 500ms

---

## 🚀 开始 Sprint 4 的步骤

### 1️⃣ 环境准备
```bash
# 创建 Sprint 4 分支
git checkout -b sprint-4-sync-and-search

# 更新依赖
pip install apscheduler sqlalchemy

# 创建必要的目录
mkdir -p src/services/sync
mkdir -p src/core/rag/filters
mkdir -p config
```

### 2️⃣ 第一个任务：Story 2.3 数据同步调度器
告诉 Claude:
```
开始 Sprint 4 - Story 2.3: 数据同步调度器的实现。
按照 SPRINT4_PLAN.md 中的设计，从 Phase 1 开始实现调度器核心。
```

### 3️⃣ 持续跟踪进度
- 每完成一个 Phase，更新本文档
- 每完成一个 Story，更新 SPRINTS.md
- 每天运行测试验证功能

---

**文档创建时间**: 2026-01-27
**维护者**: Claude Sonnet 4.5
**预计完成时间**: 2026-02-27
