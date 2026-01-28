# Sprint 5 实施计划

> **Sprint 周期**: 2026-01-29 ~ 2026-02-28 (31天)
> **总故事点数**: 34 点
> **预计完成率**: 100%
> **Sprint 目标**: 对话历史管理、文档上传完善、引用优化、部署优化

---

## 📋 Sprint 5 用户故事清单

| 序号 | 用户故事 | 故事点 | 优先级 | 预估工作量 | 依赖关系 |
|------|---------|--------|--------|-----------|---------|
| 1 | Story 5.1: 对话历史管理 | 10点 | P0 | 5-6天 | 无 |
| 2 | Story 5.2: 文档上传增强 | 8点 | P0 | 4-5天 | 无 |
| 3 | Story 5.3: 引用溯源优化 | 8点 | P1 | 3-4天 | Sprint 3 引用基础 |
| 4 | Story 5.4: Docker 部署优化 | 5点 | P1 | 2-3天 | 无 |
| 5 | Story 5.5: 性能监控面板 | 3点 | P2 | 1-2天 | 无 |

**总计**: 34 故事点，预估 15-20 工作日

---

## 🎯 Story 5.1: 对话历史管理 (10点) - P0 优先级

### 用户故事
**作为** 系统用户
**我希望** 能够保存、查看、搜索和管理我的对话历史
**以便** 回顾之前的问答内容，继续未完成的对话，找到有价值的信息

### 验收标准
- [ ] 对话自动保存到数据库
- [ ] 支持对话列表查看（按时间倒序）
- [ ] 支持对话搜索（关键词、时间范围）
- [ ] 支持对话重命名（自动生成标题 + 手动编辑）
- [ ] 支持对话删除（单个、批量）
- [ ] 支持对话导出（Markdown、JSON、PDF）
- [ ] 支持继续之前的对话
- [ ] 对话分页显示（每页 20 条）
- [ ] 显示对话统计信息（总数、今日、本周、本月）

### 技术设计

#### 1. 数据模型

```python
# src/storage/database/models.py

class Conversation(Base):
    """对话会话模型"""
    __tablename__ = "conversations"

    id: str  # UUID
    user_id: str  # 用户 ID（预留多用户支持）
    title: str  # 对话标题（自动生成或用户设置）
    created_at: datetime
    updated_at: datetime
    message_count: int  # 消息数量
    metadata: dict  # 元数据（模型、参数等）
    is_deleted: bool  # 软删除标记

class Message(Base):
    """对话消息模型"""
    __tablename__ = "messages"

    id: str  # UUID
    conversation_id: str  # 外键关联 Conversation
    role: str  # "user" | "assistant" | "system"
    content: str  # 消息内容
    contexts: list[dict]  # 检索上下文（JSON）
    citations: list[dict]  # 引用信息（JSON）
    created_at: datetime
    model_name: str  # 使用的模型
    token_count: int  # Token 数量
    metadata: dict  # 元数据
```

#### 2. 核心组件

**文件结构**:
```
src/services/conversation/
├── __init__.py
├── manager.py           # 对话管理器（ConversationManager）
├── exporter.py          # 对话导出器（支持多种格式）
├── models.py            # Pydantic 模型
└── title_generator.py   # 对话标题生成器（基于首条消息）

src/storage/database/repository/
└── conversation_repo.py # 对话数据访问层

src/api/routes/
└── conversation.py      # 对话管理 API

src/ui/pages/
└── history_page.py      # 对话历史页面
```

#### 3. API 端点设计

```python
# 对话管理
GET    /api/v1/conversations              # 获取对话列表（支持分页、过滤、搜索）
POST   /api/v1/conversations              # 创建新对话
GET    /api/v1/conversations/{id}         # 获取对话详情（包含所有消息）
PUT    /api/v1/conversations/{id}         # 更新对话（重命名）
DELETE /api/v1/conversations/{id}         # 删除对话（软删除）
POST   /api/v1/conversations/bulk-delete  # 批量删除

# 消息管理
GET    /api/v1/conversations/{id}/messages       # 获取对话消息列表
POST   /api/v1/conversations/{id}/messages       # 添加消息到对话
DELETE /api/v1/conversations/{id}/messages/{mid} # 删除单条消息

# 对话操作
POST   /api/v1/conversations/{id}/export   # 导出对话（支持格式：md/json/pdf）
POST   /api/v1/conversations/{id}/continue # 继续对话（设为活跃对话）
GET    /api/v1/conversations/search        # 搜索对话
GET    /api/v1/conversations/stats         # 获取统计信息
```

#### 4. 实现步骤

**Phase 1: 数据模型和持久化（2天）**
- [ ] 创建数据库表（conversations, messages）
- [ ] 实现 ConversationRepository
- [ ] 实现基础 CRUD 操作
- [ ] 添加数据库索引（user_id, created_at, title）
- [ ] 单元测试

**Phase 2: 对话管理服务（2天）**
- [ ] 实现 ConversationManager
  - 对话创建、更新、删除
  - 消息添加、查询
  - 对话搜索（全文搜索 title + content）
- [ ] 实现对话标题自动生成
  - 基于首条用户消息
  - 使用 LLM 生成简短标题（可选）
- [ ] 实现对话导出器
  - Markdown 格式
  - JSON 格式
  - PDF 格式（使用 reportlab）
- [ ] 单元测试

**Phase 3: API 端点（1天）**
- [ ] 实现所有 12 个 API 端点
- [ ] 请求参数验证（Pydantic）
- [ ] 错误处理和日志
- [ ] API 文档（FastAPI 自动生成）
- [ ] 集成测试

**Phase 4: UI 界面（2天）**
- [ ] 创建对话历史页面
  - 对话列表（带搜索、过滤）
  - 对话详情查看
  - 对话重命名
  - 对话删除（确认对话框）
  - 对话导出
- [ ] 集成到主 UI（新增 Tab）
- [ ] 样式优化

**Phase 5: 集成测试（0.5天）**
- [ ] 端到端测试（创建 → 查看 → 搜索 → 导出 → 删除）
- [ ] 性能测试（100+ 对话，1000+ 消息）
- [ ] 并发测试

#### 5. 对话标题生成策略

```python
# 策略 1: 基于关键词提取（快速）
def generate_title_from_keywords(first_message: str) -> str:
    """从首条消息提取关键词生成标题"""
    # 使用 jieba 分词 + TF-IDF
    keywords = extract_keywords(first_message, top_k=3)
    return " ".join(keywords)[:50]

# 策略 2: 基于 LLM 生成（准确但慢）
def generate_title_from_llm(first_message: str) -> str:
    """使用 LLM 生成对话标题"""
    prompt = f"根据以下用户问题生成简短标题（不超过20字）：\n{first_message}"
    return llm_generate(prompt, max_tokens=30)

# 策略 3: 混合策略（推荐）
def generate_title(first_message: str, use_llm: bool = False) -> str:
    """混合策略：优先使用关键词，可选 LLM 优化"""
    if len(first_message) <= 20:
        return first_message

    if use_llm:
        return generate_title_from_llm(first_message)
    else:
        return generate_title_from_keywords(first_message)
```

#### 6. 技术依赖
- **SQLAlchemy**: ORM 和数据库操作
- **jieba**: 中文分词（标题生成）
- **reportlab**: PDF 生成（可选）
- **markdown**: Markdown 格式化

---

## 🎯 Story 5.2: 文档上传增强 (8点) - P0 优先级

### 用户故事
**作为** 系统用户
**我希望** 能够上传本地文档到知识库
**以便** 将私有文档纳入问答系统，扩充知识库内容

### 验收标准
- [ ] 支持多种文档格式（PDF、DOCX、TXT、MD、HTML）
- [ ] 支持批量上传（拖拽、选择多个文件）
- [ ] 显示上传进度（单个文件、总体进度）
- [ ] 自动文档解析和索引
- [ ] 支持文档元数据编辑（标题、标签、分类）
- [ ] 上传历史记录
- [ ] 文件大小限制（单文件 < 50MB）
- [ ] 支持的总文件数量 > 1000

### 技术设计

#### 1. 核心组件

**文件结构**:
```
src/services/document/
├── __init__.py
├── upload_manager.py    # 文档上传管理器
├── parser.py            # 文档解析器（已有，增强）
└── validator.py         # 文件验证器

src/document_processing/
├── parser/
│   ├── pdf.py           # PDF 解析（PyPDF2/pdfplumber）
│   ├── docx.py          # DOCX 解析（python-docx）
│   ├── txt.py           # TXT 解析
│   └── markdown.py      # Markdown 解析

src/api/routes/
└── upload.py            # 文档上传 API

src/ui/pages/
└── upload_page.py       # 文档上传页面（增强）
```

#### 2. API 端点设计

```python
# 文档上传
POST   /api/v1/documents/upload         # 上传文档（支持 multipart/form-data）
POST   /api/v1/documents/upload/batch   # 批量上传
GET    /api/v1/documents/upload/status  # 获取上传状态（基于任务 ID）

# 文档管理（已有，需增强）
GET    /api/v1/documents                # 获取文档列表
GET    /api/v1/documents/{id}           # 获取文档详情
PUT    /api/v1/documents/{id}/metadata  # 更新元数据
DELETE /api/v1/documents/{id}           # 删除文档

# 文档解析
POST   /api/v1/documents/parse          # 解析文档预览（不索引）
GET    /api/v1/documents/supported-formats  # 获取支持的格式列表
```

#### 3. 实现步骤

**Phase 1: 文档解析器增强（2天）**
- [ ] 完善 PDF 解析
  - 文本提取（PyPDF2）
  - 表格提取（pdfplumber）
  - 图片提取（可选）
- [ ] 完善 DOCX 解析
  - 文本、表格、样式
- [ ] 实现 Markdown 解析
- [ ] 实现 HTML 解析
- [ ] 文件验证器
  - 格式验证
  - 大小限制
  - 病毒扫描（可选）
- [ ] 单元测试

**Phase 2: 上传管理器（2天）**
- [ ] 实现 UploadManager
  - 文件接收和保存
  - 异步文档解析
  - 自动索引到向量数据库
  - 元数据提取和保存
- [ ] 实现上传进度跟踪
  - 使用后台任务
  - SSE 实时推送进度
- [ ] 实现批量上传
  - 并发处理（最多 5 个文件）
  - 错误处理和重试
- [ ] 单元测试

**Phase 3: API 端点（1天）**
- [ ] 实现上传 API
- [ ] 集成测试

**Phase 4: UI 增强（2天）**
- [ ] 增强文档上传页面
  - 拖拽上传
  - 多文件选择
  - 实时进度条
  - 上传历史
  - 元数据编辑
- [ ] 样式优化

**Phase 5: 测试（1天）**
- [ ] 各格式文档测试
- [ ] 大文件测试
- [ ] 并发上传测试

#### 4. 文档解析示例

```python
# PDF 解析
class PDFParser:
    def parse(self, file_path: str) -> ParsedDocument:
        """解析 PDF 文档"""
        text = self._extract_text(file_path)
        tables = self._extract_tables(file_path)
        metadata = self._extract_metadata(file_path)

        return ParsedDocument(
            content=text,
            tables=tables,
            metadata=metadata,
            page_count=self._get_page_count(file_path)
        )

# DOCX 解析
class DOCXParser:
    def parse(self, file_path: str) -> ParsedDocument:
        """解析 DOCX 文档"""
        doc = Document(file_path)

        text = "\n".join([p.text for p in doc.paragraphs])
        tables = self._extract_tables(doc)
        metadata = self._extract_metadata(doc)

        return ParsedDocument(
            content=text,
            tables=tables,
            metadata=metadata
        )
```

#### 5. 技术依赖
- **PyPDF2**: PDF 文本提取
- **pdfplumber**: PDF 表格提取
- **python-docx**: DOCX 解析
- **markdown**: Markdown 解析
- **BeautifulSoup4**: HTML 解析
- **python-magic**: 文件类型检测

---

## 🎯 Story 5.3: 引用溯源优化 (8点) - P1 优先级

### 用户故事
**作为** 系统用户
**我希望** 看到更清晰、更详细的引用信息
**以便** 快速验证答案的准确性，并跳转到原始文档

### 验收标准
- [ ] 引用信息完整展示（来源、链接、相关度分数）
- [ ] 支持一键跳转到原文
- [ ] 显示引用文本片段（带关键词高亮）
- [ ] 引用按相关度排序
- [ ] 支持引用过滤（按来源类型）
- [ ] 引用统计信息（使用频率、质量分数）
- [ ] 引用缓存优化（减少重复计算）

### 技术设计

#### 1. 核心功能增强

**文件**:
```
src/core/rag/
├── citation.py          # 引用系统（已有，优化）
└── citation_cache.py    # 引用缓存（新增）

src/ui/components/
└── citation_display.py  # 引用展示组件
```

#### 2. 实现步骤

**Phase 1: 引用系统优化（2天）**
- [ ] 优化 Citation 数据模型
  - 添加更多元数据
  - 文本片段提取
  - 关键词位置标记
- [ ] 实现引用缓存
  - Redis 缓存
  - 30 分钟 TTL
- [ ] 引用质量评分
  - 基于相关度、新鲜度、来源可靠性

**Phase 2: UI 优化（1.5天）**
- [ ] 优化引用展示组件
  - 折叠/展开
  - 关键词高亮
  - 一键复制引用
  - 一键跳转
- [ ] 引用统计面板

**Phase 3: 测试（0.5天）**
- [ ] 功能测试
- [ ] 性能测试

---

## 🎯 Story 5.4: Docker 部署优化 (5点) - P1 优先级

### 用户故事
**作为** 系统管理员
**我希望** 能够使用 Docker 快速部署整个系统
**以便** 简化部署流程，提高环境一致性

### 验收标准
- [ ] 完善 Dockerfile（多阶段构建）
- [ ] 优化 docker-compose.yml（包含所有服务）
- [ ] 提供环境变量配置模板
- [ ] 数据持久化配置（Volume）
- [ ] 健康检查配置
- [ ] 日志收集配置
- [ ] 部署文档完善

### 实现步骤

**Phase 1: Dockerfile 优化（1天）**
- [ ] 多阶段构建
- [ ] 减小镜像大小
- [ ] 添加健康检查

**Phase 2: Docker Compose 完善（1天）**
- [ ] 包含所有服务
  - KT-BOT 主应用
  - PostgreSQL
  - Redis
  - Ollama（可选）
- [ ] 网络配置
- [ ] Volume 配置
- [ ] 环境变量模板

**Phase 3: 部署文档（1天）**
- [ ] 快速开始指南
- [ ] 配置说明
- [ ] 常见问题

---

## 🎯 Story 5.5: 性能监控面板 (3点) - P2 优先级

### 用户故事
**作为** 系统管理员
**我希望** 能够监控系统性能指标
**以便** 及时发现和解决性能问题

### 验收标准
- [ ] 实时显示系统指标（CPU、内存、磁盘）
- [ ] 显示 API 响应时间
- [ ] 显示数据库连接数
- [ ] 显示检索性能指标
- [ ] 简单的监控面板 UI

### 实现步骤

**Phase 1: 指标收集（1天）**
- [ ] 系统指标采集
- [ ] API 性能监控

**Phase 2: 监控面板（1天）**
- [ ] 简单的 Gradio 监控页面
- [ ] 实时刷新

---

## 📅 Sprint 5 时间规划

### 开发顺序（按优先级和依赖）

**第 1 周（2026-01-29 ~ 2026-02-04）**:
- Day 1-3: Story 5.1 Phase 1-2（对话历史数据模型和服务）
- Day 4-5: Story 5.2 Phase 1（文档解析器增强）
- Day 6-7: Story 5.1 Phase 3-4（对话历史 API 和 UI）

**第 2 周（2026-02-05 ~ 2026-02-11）**:
- Day 8-10: Story 5.2 Phase 2-3（上传管理器和 API）
- Day 11-12: Story 5.2 Phase 4（UI 增强）
- Day 13-14: Story 5.3 Phase 1-2（引用优化）

**第 3 周（2026-02-12 ~ 2026-02-18）**:
- Day 15-16: Story 5.4（Docker 部署优化）
- Day 17-18: Story 5.5（性能监控面板）
- Day 19: 集成测试

**第 4 周（2026-02-19 ~ 2026-02-28）**:
- Day 20-22: Bug 修复和优化
- Day 23-25: 文档更新
- Day 26-27: 端到端测试
- Day 28: Sprint 回顾和 v0.3.0 发布准备

---

## ✅ Sprint 5 验收标准

### 功能验收
- [ ] 对话历史管理完整可用
- [ ] 文档上传支持多种格式
- [ ] 引用信息清晰展示
- [ ] Docker 部署流畅
- [ ] 性能监控面板可用

### 技术验收
- [ ] 所有单元测试通过（新增 50+ 测试）
- [ ] 集成测试通过
- [ ] 代码覆盖率 > 75%（整体）
- [ ] API 文档更新完整
- [ ] 部署文档完善

### 质量验收
- [ ] 无 P0/P1 Bug
- [ ] 对话查询性能 < 200ms（1000 条对话）
- [ ] 文档上传性能 < 5s（10MB PDF）
- [ ] 内存占用 < 2GB
- [ ] Docker 镜像大小 < 2GB

---

## 🚀 开始 Sprint 5 的步骤

### 1️⃣ 环境准备

```bash
# 创建 Sprint 5 分支
git checkout -b sprint-5-history-and-upload

# 更新依赖
pip install PyPDF2 pdfplumber python-docx jieba reportlab python-magic

# 创建必要的目录
mkdir -p src/services/conversation
mkdir -p src/services/document
mkdir -p src/ui/pages
```

### 2️⃣ 数据库迁移

```bash
# 创建对话表迁移
alembic revision -m "Add conversation and message tables"

# 执行迁移
alembic upgrade head
```

### 3️⃣ 第一个任务：Story 5.1 对话历史管理

告诉 Claude:
```
开始 Sprint 5 - Story 5.1: 对话历史管理的实现。
按照 SPRINT5_PLAN.md 中的设计，从 Phase 1 开始实现数据模型和持久化。
```

### 4️⃣ 持续跟踪进度
- 每完成一个 Phase，更新本文档
- 每完成一个 Story，创建完成总结文档
- 每天运行测试验证功能

---

## 📊 Sprint 5 与之前 Sprint 的对比

| 维度 | Sprint 2 | Sprint 4 | Sprint 5 |
|------|---------|---------|---------|
| **主题** | 混合检索 | 数据同步 | 对话管理 |
| **故事点** | 29 点 | 35 点 | 34 点 |
| **工作量** | 2 周 | 4 周 | 4 周 |
| **新增代码** | ~4,000 行 | ~2,800 行 | ~3,000 行（预计）|
| **API 端点** | 7+ 个 | 15+ 个 | 15+ 个 |
| **UI 页面** | 1 个 | 3 个 | 2 个 |
| **核心价值** | 提升检索质量 | 自动化同步 | 用户体验 |

---

## 🎯 Sprint 5 成功标准

### 用户价值
- ✅ 用户可以查看和管理所有对话历史
- ✅ 用户可以上传本地文档到知识库
- ✅ 用户可以看到清晰的引用来源
- ✅ 管理员可以快速 Docker 部署
- ✅ 管理员可以监控系统性能

### 技术目标
- ✅ 完整的对话持久化和管理系统
- ✅ 多格式文档解析和上传
- ✅ 优化的引用展示
- ✅ 生产就绪的 Docker 部署
- ✅ 基础性能监控

### 里程碑
- **Week 1**: 对话历史基础完成
- **Week 2**: 文档上传功能完成
- **Week 3**: 引用优化和部署完成
- **Week 4**: 测试和发布 v0.3.0

---

**文档创建时间**: 2026-01-28
**维护者**: Claude Sonnet 4.5
**预计完成时间**: 2026-02-28
**版本**: v0.3.0-planning
