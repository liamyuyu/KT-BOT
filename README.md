# KT BOT

<p align="center">
  <img src="https://img.shields.io/badge/Ollama-Powered-blue" alt="Ollama">
  <img src="https://img.shields.io/badge/MCP-Integrated-green" alt="MCP">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-orange" alt="License">
</p>

<p align="center">
  <strong>基于本地 Ollama 模型的企业级智能知识库问答系统</strong>
</p>

<p align="center">
  集成 Jira 和 Confluence，通过 MCP 协议提供私有化部署的 AI 对话服务
</p>

---

## 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [为什么选择 KT BOT](#为什么选择-kt-bot)
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细配置](#详细配置)
- [使用指南](#使用指南)
- [项目结构](#项目结构)
- [开发指南](#开发指南)
- [部署方案](#部署方案)
- [常见问题](#常见问题)
- [路线图](#路线图)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [致谢](#致谢)

---

## 项目简介

**KT BOT** 是一个受 [Kotaemon](https://github.com/Cinnamon/kotaemon) 启发的智能知识库问答系统，专为企业团队设计。它利用本地部署的 Ollama 大语言模型，结合 **Model Context Protocol (MCP)**，无缝连接 Jira 和 Confluence 等企业工具，为团队提供基于自有知识库的 AI 问答服务。

### 设计目标

KT BOT 致力于解决企业在使用 AI 问答系统时的核心痛点：

1. **数据隐私** - 完全本地部署，敏感数据不离开企业环境
2. **知识整合** - 自动聚合分散在 Jira、Confluence 中的企业知识
3. **实时同步** - 与企业工具保持实时数据同步，信息始终最新
4. **易于扩展** - 基于 MCP 协议，轻松添加新的数据源和功能

### 与 Kotaemon 的关系

KT BOT 借鉴了 Kotaemon 的优秀设计理念，并针对企业场景进行了优化：

| 特性 | Kotaemon | KT BOT |
|------|----------|--------|
| **数据源** | 静态文档上传 | 动态企业工具集成 |
| **部署方式** | 本地文档问答 | 企业级知识库系统 |
| **数据同步** | 手动上传 | 自动实时同步 |
| **扩展性** | 配置驱动 | MCP 协议驱动 |
| **目标用户** | 个人/小团队 | 中大型企业团队 |

更多关于 Kotaemon 的详细信息，请查看 [Kotaemon.md](./Kotaemon.md)。

---

## 核心特性

### 🔐 隐私优先

- **完全本地部署** - 基于 Ollama，所有 AI 推理在本地完成
- **数据不出域** - 企业数据完全在私有环境中处理
- **自主可控** - 无需依赖第三方云服务
- **合规友好** - 满足 GDPR、等保等合规要求

### 🔌 企业工具集成

- **Jira 集成** - 实时同步 Issues、Comments、Attachments
- **Confluence 集成** - 自动索引 Spaces、Pages、Attachments
- **实时更新** - 增量同步机制，保持数据最新
- **权限继承** - 遵循原系统的访问权限设置

### 🧠 智能 RAG 检索

- **混合检索** - 结合向量检索和全文检索（BM25）
- **语义理解** - 使用中文优化的 Embedding 模型
- **重排序优化** - Cross-Encoder 二次排序，提升准确率
- **引用溯源** - 清晰标注信息来源，支持跳转原文

### 🎨 简洁易用的界面

- **Kotaemon 风格 UI** - 清洁、现代化的对话界面
- **多模型支持** - 自由切换不同的 Ollama 模型
- **对话管理** - 支持多轮对话、历史记录管理
- **实时反馈** - 流式响应，打字机效果展示

### 🔧 灵活扩展

- **MCP 协议** - 标准化的扩展接口
- **插件式架构** - 轻松添加新的数据源
- **自定义 Tools** - 开发自己的 MCP Tools
- **开源透明** - 完整的代码和文档，社区驱动

---

## 技术架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     Web UI Layer (Gradio)                   │
│  ┌──────────────┬──────────────┬──────────────────────────┐ │
│  │ Chat         │ Document     │ Settings                 │ │
│  │ Interface    │ Management   │ Panel                    │ │
│  └──────────────┴──────────────┴──────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    Application Layer                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ FastAPI Gateway                                      │   │
│  │ - Authentication & Authorization                     │   │
│  │ - Session Management                                 │   │
│  │ - API Routing                                        │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
┌───────▼──────────┐                   ┌───────▼──────────┐
│   RAG Engine     │                   │   MCP Server     │
│                  │                   │                  │
│ ┌──────────────┐ │                   │ ┌──────────────┐ │
│ │ Query        │ │                   │ │ Jira Tool    │ │
│ │ Processing   │ │                   │ │              │ │
│ └──────────────┘ │                   │ └──────────────┘ │
│                  │                   │                  │
│ ┌──────────────┐ │                   │ ┌──────────────┐ │
│ │ Hybrid       │ │                   │ │ Confluence   │ │
│ │ Retrieval    │ │                   │ │ Tool         │ │
│ └──────────────┘ │                   │ └──────────────┘ │
│                  │                   │                  │
│ ┌──────────────┐ │                   │ ┌──────────────┐ │
│ │ Re-ranking   │ │                   │ │ Custom       │ │
│ │              │ │                   │ │ Tools        │ │
│ └──────────────┘ │                   │ └──────────────┘ │
│                  │                   │                  │
│ ┌──────────────┐ │                   └──────────────────┘
│ │ Response     │ │
│ │ Generation   │ │
│ └──────────────┘ │
└───────┬──────────┘
        │
┌───────▼─────────────────────────────────────────────────────┐
│                      Data Layer                             │
│  ┌────────────────┬─────────────────┬────────────────────┐  │
│  │ Vector Store   │ Full-text       │ Document Storage   │  │
│  │ (ChromaDB/     │ Search          │ (PostgreSQL)       │  │
│  │  Qdrant)       │ (Elasticsearch) │                    │  │
│  └────────────────┴─────────────────┴────────────────────┘  │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                    External Services                        │
│  ┌──────────────┬──────────────────┬────────────────────┐   │
│  │ Ollama       │ Jira API         │ Confluence API     │   │
│  │ (Local LLM)  │                  │                    │   │
│  └──────────────┴──────────────────┴────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件说明

#### 1. **Web UI Layer**
基于 Gradio 构建的用户界面层：
- **对话界面** - 类似 ChatGPT 的聊天体验
- **文档管理** - 查看和管理已同步的文档
- **设置面板** - 配置模型、数据源、检索参数

#### 2. **RAG Engine**
检索增强生成引擎：
- **查询处理** - 查询改写、扩展、分解
- **混合检索** - 向量检索（语义相似）+ 全文检索（关键词匹配）
- **重排序** - 使用 Cross-Encoder 优化结果相关性
- **响应生成** - 结合检索结果，生成准确回答

#### 3. **MCP Server**
Model Context Protocol 服务器：
- **Jira Tool** - 提供 Jira 数据访问能力
- **Confluence Tool** - 提供 Confluence 数据访问能力
- **扩展机制** - 支持自定义 Tools 开发

#### 4. **Data Layer**
数据存储层：
- **向量数据库** - 存储文档的向量表示（ChromaDB/Qdrant）
- **全文搜索** - 支持关键词检索（Elasticsearch）
- **文档存储** - 存储原始文档和元数据（PostgreSQL）

---

## 为什么选择 KT BOT

### 对比其他方案

#### vs. 纯文档上传系统（如 Kotaemon）

**KT BOT 优势**：
- ✅ 自动同步企业工具，无需手动上传
- ✅ 数据始终保持最新
- ✅ 支持大规模文档库
- ✅ 权限控制自动继承

#### vs. 云端 AI 服务（如 ChatGPT Enterprise）

**KT BOT 优势**：
- ✅ 完全私有化部署，数据安全
- ✅ 无需支付高额订阅费用
- ✅ 不受网络限制
- ✅ 自主可控，无依赖风险

#### vs. 自建 RAG 系统

**KT BOT 优势**：
- ✅ 开箱即用，快速部署
- ✅ 经过优化的检索策略
- ✅ 完善的企业工具集成
- ✅ 活跃的社区支持

### 适用场景

✅ **适合使用 KT BOT**：
- 使用 Jira/Confluence 管理项目和文档的团队
- 对数据隐私有严格要求的企业
- 需要快速搭建内部知识库的团队
- 希望降低 AI 服务成本的组织

❌ **不太适合**：
- 文档量很小（<100 个文档）的场景
- 不使用 Jira/Confluence 的团队（除非愿意扩展）
- 对 AI 响应速度要求极高的场景（云端模型更快）

---

## 系统要求

### 硬件要求

#### 最低配置
- **CPU**: 4 核
- **内存**: 8GB RAM
- **存储**: 20GB 可用空间
- **操作系统**: macOS, Linux, Windows (WSL2)

#### 推荐配置
- **CPU**: 8 核以上
- **内存**: 16GB+ RAM
- **存储**: 50GB+ SSD
- **GPU**: 支持 CUDA 的显卡（可选，用于加速）

### 软件依赖

- **Python**: 3.10 或以上
- **Ollama**: 最新稳定版
- **Docker**: 20.10+ (可选，用于容器化部署)
- **PostgreSQL**: 14+ (或使用 Docker)
- **Elasticsearch**: 8.0+ (可选，用于全文检索)

---

## 快速开始

### 方法一：本地安装（推荐用于开发）

#### 1. 安装 Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows (WSL2)
curl -fsSL https://ollama.ai/install.sh | sh
```

启动 Ollama 服务：
```bash
ollama serve
```

拉取推荐模型：
```bash
# 中文优化模型（推荐）
ollama pull qwen2.5:7b

# 或使用 LLaMA 3.1
ollama pull llama3.1:8b

# Embedding 模型
ollama pull bge-large-zh
```

#### 2. 克隆项目

```bash
git clone https://github.com/yourusername/KT-BOT.git
cd KT-BOT
```

#### 3. 创建虚拟环境

```bash
python -m venv venv

# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

#### 4. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装开发依赖（可选）
pip install -r requirements-dev.txt
```

#### 5. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用你喜欢的编辑器
```

在 `.env` 中填入以下配置：

```env
# Ollama 配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_EMBEDDING_MODEL=bge-large-zh

# Jira 配置
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token_here

# Confluence 配置
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your_confluence_api_token_here

# 数据库配置
DATABASE_URL=postgresql://localhost:5432/ktbot
REDIS_URL=redis://localhost:6379/0

# 向量数据库配置
VECTOR_STORE=chromadb
VECTOR_STORE_PATH=./data/vectordb

# 应用配置
LOG_LEVEL=INFO
PORT=7860
HOST=0.0.0.0
```

#### 6. 初始化数据库

```bash
# 启动 PostgreSQL (使用 Docker)
docker run -d \
  --name ktbot-postgres \
  -e POSTGRES_DB=ktbot \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:14

# 运行数据库迁移
python scripts/init_db.py
```

#### 7. 启动服务

```bash
# 启动 MCP 服务器（新终端）
python src/mcp_server.py

# 启动主应用
python src/main.py
```

#### 8. 访问应用

打开浏览器访问：`http://localhost:7860`

---

### 方法二：Docker 部署（推荐用于生产）

#### 1. 使用 Docker Compose 一键启动

```bash
# 克隆项目
git clone https://github.com/yourusername/KT-BOT.git
cd KT-BOT

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的配置

# 启动所有服务
docker-compose up -d
```

#### 2. 查看服务状态

```bash
docker-compose ps
```

#### 3. 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f ktbot
```

#### 4. 停止服务

```bash
docker-compose down
```

---

## 详细配置

### 获取 Jira API Token

1. 登录你的 Atlassian 账号
2. 访问 [API Tokens 管理页面](https://id.atlassian.com/manage-profile/security/api-tokens)
3. 点击 **Create API token**
4. 输入标签（如 "KT BOT"）
5. 复制生成的 Token 并保存到 `.env` 文件

### 获取 Confluence API Token

Confluence 使用与 Jira 相同的 API Token。

### 模型选择指南

KT BOT 支持所有 Ollama 模型，以下是针对不同场景的推荐：

#### 中文场景（推荐）

| 模型 | 内存需求 | 特点 | 适用场景 |
|------|---------|------|---------|
| **qwen2.5:7b** | 8GB | 中文优化，速度快 | 日常使用（推荐） |
| qwen2.5:14b | 16GB | 更高准确率 | 准确性要求高 |
| qwen2.5:32b | 32GB | 最佳性能 | 服务器部署 |

#### 英文场景

| 模型 | 内存需求 | 特点 | 适用场景 |
|------|---------|------|---------|
| **llama3.1:8b** | 8GB | 平衡性能 | 日常使用 |
| llama3.1:70b | 40GB | 高性能 | 大规模部署 |
| mistral:7b | 8GB | 速度优先 | 快速响应 |

#### Embedding 模型

| 模型 | 语言 | 维度 | 特点 |
|------|------|------|------|
| **bge-large-zh** | 中文 | 1024 | 中文最佳（推荐） |
| nomic-embed-text | 多语言 | 768 | 多语言支持 |
| mxbai-embed-large | 英文 | 1024 | 英文优秀 |

### 向量数据库选择

#### ChromaDB（推荐）
```env
VECTOR_STORE=chromadb
VECTOR_STORE_PATH=./data/chromadb
```

**优势**：
- 易于安装，无需额外服务
- 适合中小规模部署
- Python 原生支持

#### Qdrant
```env
VECTOR_STORE=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your_api_key
```

**优势**：
- 高性能，支持大规模数据
- 丰富的过滤功能
- 生产级稳定性

#### Milvus
```env
VECTOR_STORE=milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

**优势**：
- 企业级性能
- 分布式支持
- 功能最全面

### 检索参数优化

在 `config/retrieval.yaml` 中调整检索参数：

```yaml
retrieval:
  # 混合检索权重
  hybrid_search:
    vector_weight: 0.7      # 向量检索权重（语义理解）
    fulltext_weight: 0.3    # 全文检索权重（关键词匹配）

  # 检索数量
  retrieval_k: 20           # 初始检索文档数
  rerank_k: 5               # 重排序后保留数

  # 相似度阈值
  similarity_threshold: 0.6 # 低于此分数的结果将被过滤

  # 重排序配置
  reranker:
    enabled: true
    model: "bge-reranker-large"
    device: "cpu"           # 或 "cuda"
```

---

## 使用指南

### 基础问答

#### 查询 Jira Issues

```
问：有哪些高优先级的 bug 还没解决？
答：根据 Jira 数据，当前有 3 个高优先级未解决的 bug：

1. [KT-123] 用户登录失败
   优先级: High | 状态: In Progress
   负责人: @张三
   链接: https://your-jira.com/browse/KT-123

2. [KT-145] 数据导出异常
   优先级: High | 状态: Open
   负责人: 未分配
   链接: https://your-jira.com/browse/KT-145

3. [KT-167] API 响应超时
   优先级: High | 状态: In Review
   负责人: @李四
   链接: https://your-jira.com/browse/KT-167

【来源】Jira 项目: KT-PROJECT | 查询时间: 2025-12-30
```

#### 搜索 Confluence 文档

```
问：关于用户认证的文档在哪里？
答：在 Confluence 中找到以下相关文档：

1. 用户认证系统设计文档
   位置: 技术文档 > 系统架构 > 认证系统
   最后更新: 2025-11-15
   链接: https://your-confluence.com/...

   摘要: 本文档描述了基于 JWT 的用户认证流程...

2. API 认证接口说明
   位置: API 文档 > 认证接口
   最后更新: 2025-12-01
   链接: https://your-confluence.com/...

   摘要: 提供了完整的认证 API 使用示例...

【来源】Confluence Space: 技术文档
```

### 高级功能

#### 跨平台检索

```
问：关于支付功能的所有信息
答：我在 Jira 和 Confluence 中找到了相关信息：

【Jira Issues】
- [PAY-45] 支付接口集成 (已完成)
- [PAY-67] 支付回调优化 (进行中)

【Confluence 文档】
- 支付系统技术方案
- 支付接口对接指南
- 支付测试用例

【代码仓库】（如果集成了 GitLab）
- payment_service.py
- payment_webhook_handler.py

需要我详细介绍哪个方面？
```

#### 复杂问题推理

```
问：过去一个月哪个模块的 bug 最多？为什么？
答：让我分析一下过去一个月的 Jira 数据...

【分析结果】
1. Bug 数量排名：
   - 用户中心模块: 15 个
   - 支付模块: 8 个
   - 搜索模块: 6 个

2. 用户中心模块 Bug 多的原因：
   根据 Jira 评论和 Confluence 文档分析：

   a) 近期重构: 在 11月进行了大规模重构
      [来源: CONF-123 "用户中心重构方案"]

   b) 新功能上线: 新增了社交登录功能
      [来源: JIRA-456 "集成第三方登录"]

   c) 测试覆盖不足: 测试用例覆盖率仅 60%
      [来源: CONF-789 "测试报告-11月"]

【建议】
1. 增加该模块的测试覆盖率
2. 进行代码审查，提升代码质量
3. 考虑增加集成测试

【数据来源】
- Jira 项目: 2025-11-30 至 2025-12-30
- Confluence 技术文档和测试报告
```

#### 引用溯源

每个回答都会显示信息来源：

```
【引用来源】
1. 📄 员工手册.pdf - 第 15 页
   相关度: 95%
   "员工享有每年 15 天带薪年假..."
   [查看原文]

2. 🔗 JIRA-123: 假期管理系统优化
   相关度: 87%
   "根据新的假期政策..."
   [打开 Issue]

3. 📋 HR 政策 - Confluence
   相关度: 82%
   "年假计算方式：入职满一年后..."
   [查看文档]
```

### 对话管理

#### 创建新对话

点击界面上的 "新建对话" 按钮，或使用快捷键 `Ctrl + N`

#### 查看历史对话

1. 点击左侧 "历史记录" 标签
2. 按日期或关键词搜索
3. 点击对话标题继续之前的对话

#### 导出对话

1. 选择要导出的对话
2. 点击 "导出" 按钮
3. 选择格式：Markdown / PDF / JSON

---

## 项目结构

本项目结构按照 Requirements.md 中定义的 9 个 Epic 组织，确保代码模块化和可维护性。

```
KT-BOT/
├── .github/
│   └── workflows/              # GitHub Actions CI/CD
│       ├── test.yml            # 自动化测试
│       ├── lint.yml            # 代码检查
│       └── deploy.yml          # 自动化部署
│
├── config/                     # 配置文件目录
│   ├── logging.yaml            # 日志配置
│   ├── retrieval.yaml          # 检索参数配置（Epic 3, 9）
│   ├── models.yaml             # 模型配置（Epic 1）
│   ├── sync.yaml               # 数据同步配置（Epic 2）
│   └── auth.yaml               # 认证配置（Epic 6）
│
├── data/                       # 数据目录（.gitignore）
│   ├── vectordb/               # 向量数据库文件
│   ├── documents/              # 原始文档存储
│   ├── uploads/                # 用户上传文件
│   ├── cache/                  # 缓存文件
│   └── logs/                   # 应用日志
│
├── docs/                       # 项目文档
│   ├── Kotaemon.md             # Kotaemon 参考文档
│   ├── Requirements.md         # 需求文档（Epic 定义）
│   ├── SPRINTS.md              # Sprint 规划
│   ├── CHANGELOG.md            # 版本变更日志
│   ├── API.md                  # API 接口文档
│   ├── DEVELOPMENT.md          # 开发者指南
│   └── DEPLOYMENT.md           # 部署文档
│
├── scripts/                    # 工具脚本
│   ├── init_db.py              # 数据库初始化
│   ├── sync_jira.py            # 手动同步 Jira（Epic 2）
│   ├── sync_confluence.py      # 手动同步 Confluence（Epic 2）
│   ├── index_documents.py      # 批量索引文档（Epic 3）
│   ├── benchmark.py            # 性能测试（Epic 8）
│   └── backup.py               # 数据备份
│
├── src/                        # 源代码根目录
│   ├── api/                    # REST API 层
│   │   ├── __init__.py
│   │   ├── routes/             # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证接口（Epic 6）
│   │   │   ├── chat.py         # 对话接口（Epic 4）
│   │   │   ├── documents.py    # 文档管理接口（Epic 4）
│   │   │   ├── models.py       # 模型管理接口（Epic 1）
│   │   │   ├── sync.py         # 同步管理接口（Epic 2）
│   │   │   └── admin.py        # 管理员接口（Epic 6）
│   │   │
│   │   ├── middleware/         # 中间件
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证中间件
│   │   │   ├── rate_limit.py   # 限流中间件
│   │   │   └── logging.py      # 日志中间件
│   │   │
│   │   └── schemas/            # API Schema（Pydantic）
│   │       ├── __init__.py
│   │       ├── chat.py
│   │       ├── document.py
│   │       └── user.py
│   │
│   ├── auth/                   # 【Epic 6】认证与权限管理
│   │   ├── __init__.py
│   │   ├── authentication.py   # 用户认证（JWT/OAuth）
│   │   ├── authorization.py    # 权限控制（RBAC）
│   │   ├── session.py          # 会话管理
│   │   ├── quota.py            # 使用配额管理
│   │   └── models.py           # 用户/角色模型
│   │
│   ├── core/                   # 核心业务逻辑
│   │   ├── __init__.py
│   │   │
│   │   ├── llm/                # 【Epic 1】大语言模型管理
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # 模型基类
│   │   │   ├── ollama.py       # Ollama 模型集成
│   │   │   ├── manager.py      # 多模型管理
│   │   │   ├── health.py       # 模型健康检查
│   │   │   └── recommender.py  # 智能模型推荐
│   │   │
│   │   ├── embedding/          # 【Epic 1】Embedding 模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Embedding 基类
│   │   │   ├── ollama.py       # Ollama Embedding
│   │   │   └── manager.py      # Embedding 模型管理
│   │   │
│   │   ├── rag/                # 【Epic 3】RAG 检索引擎
│   │   │   ├── __init__.py
│   │   │   ├── indexer.py      # 文档索引器
│   │   │   ├── chunker.py      # 文档分块器（Epic 9）
│   │   │   ├── retriever/      # 检索器模块
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py     # 检索器基类
│   │   │   │   ├── vector.py   # 向量检索
│   │   │   │   ├── bm25.py     # BM25 全文检索
│   │   │   │   └── hybrid.py   # 混合检索（RRF）
│   │   │   │
│   │   │   ├── reranker.py     # Cross-Encoder 重排序
│   │   │   ├── query_processor.py  # 查询处理与扩展
│   │   │   ├── citation.py     # 引用溯源系统
│   │   │   ├── filter.py       # 检索结果过滤
│   │   │   ├── pipeline.py     # RAG 完整管道
│   │   │   └── visualizer.py   # 检索可视化（Epic 3）
│   │   │
│   │   └── generator/          # 【Epic 3】响应生成
│   │       ├── __init__.py
│   │       ├── base.py         # 生成器基类
│   │       ├── stream.py       # 流式生成
│   │       └── prompt.py       # Prompt 模板管理
│   │
│   ├── document_processing/    # 【Epic 7】文档处理与 OCR
│   │   ├── __init__.py
│   │   ├── parser/             # 文档解析器
│   │   │   ├── __init__.py
│   │   │   ├── pdf.py          # PDF 解析
│   │   │   ├── docx.py         # Word 解析
│   │   │   ├── markdown.py     # Markdown 解析
│   │   │   └── html.py         # HTML 解析
│   │   │
│   │   ├── ocr/                # OCR 引擎
│   │   │   ├── __init__.py
│   │   │   ├── tesseract.py    # Tesseract OCR
│   │   │   └── paddleocr.py    # PaddleOCR
│   │   │
│   │   ├── table_extractor.py  # 表格提取
│   │   ├── image_processor.py  # 图片处理
│   │   └── cleaner.py          # 文本清洗
│   │
│   ├── integrations/           # 【Epic 2】企业工具集成
│   │   ├── __init__.py
│   │   │
│   │   ├── jira/               # Jira 集成
│   │   │   ├── __init__.py
│   │   │   ├── client.py       # Jira API 客户端
│   │   │   ├── sync.py         # 数据同步逻辑
│   │   │   ├── parser.py       # Issue/Comment 解析
│   │   │   └── webhook.py      # Webhook 处理
│   │   │
│   │   ├── confluence/         # Confluence 集成
│   │   │   ├── __init__.py
│   │   │   ├── client.py       # Confluence API 客户端
│   │   │   ├── sync.py         # 页面同步逻辑
│   │   │   ├── parser.py       # 页面内容解析
│   │   │   └── webhook.py      # Webhook 处理
│   │   │
│   │   └── scheduler.py        # 同步调度器
│   │
│   ├── mcp/                    # 【Epic 5】MCP 协议支持
│   │   ├── __init__.py
│   │   ├── server.py           # MCP Server 主程序
│   │   ├── protocol.py         # MCP 协议实现
│   │   │
│   │   ├── tools/              # MCP Tools
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Tool 基类
│   │   │   ├── jira_tool.py    # Jira MCP Tool
│   │   │   ├── confluence_tool.py  # Confluence MCP Tool
│   │   │   └── custom_tool.py  # 自定义 Tool 示例
│   │   │
│   │   ├── registry.py         # Tool 注册中心
│   │   └── config.json         # MCP 配置文件
│   │
│   ├── models/                 # 数据模型（ORM）
│   │   ├── __init__.py
│   │   ├── base.py             # 模型基类
│   │   ├── document.py         # 文档模型
│   │   ├── conversation.py     # 对话模型
│   │   ├── message.py          # 消息模型
│   │   ├── user.py             # 用户模型
│   │   ├── role.py             # 角色模型
│   │   ├── citation.py         # 引用模型
│   │   └── sync_log.py         # 同步日志模型
│   │
│   ├── monitoring/             # 【Epic 8】性能监控与告警
│   │   ├── __init__.py
│   │   ├── metrics.py          # Prometheus 指标
│   │   ├── tracer.py           # OpenTelemetry 追踪
│   │   ├── profiler.py         # 性能分析
│   │   ├── alerting.py         # 告警系统
│   │   └── dashboard.py        # 监控仪表盘
│   │
│   ├── storage/                # 存储层
│   │   ├── __init__.py
│   │   │
│   │   ├── vector/             # 向量数据库
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # 向量存储基类
│   │   │   ├── chromadb.py     # ChromaDB 实现
│   │   │   ├── qdrant.py       # Qdrant 实现
│   │   │   └── milvus.py       # Milvus 实现
│   │   │
│   │   ├── database/           # 关系数据库
│   │   │   ├── __init__.py
│   │   │   ├── engine.py       # 数据库引擎
│   │   │   ├── session.py      # 会话管理
│   │   │   ├── migrations/     # Alembic 迁移
│   │   │   │   └── versions/
│   │   │   └── repository/     # 数据访问层
│   │   │       ├── __init__.py
│   │   │       ├── document_repo.py
│   │   │       ├── user_repo.py
│   │   │       └── conversation_repo.py
│   │   │
│   │   ├── cache/              # 缓存层
│   │   │   ├── __init__.py
│   │   │   ├── redis.py        # Redis 缓存
│   │   │   └── memory.py       # 内存缓存
│   │   │
│   │   └── file_storage/       # 文件存储
│   │       ├── __init__.py
│   │       ├── local.py        # 本地文件系统
│   │       └── s3.py           # S3 兼容存储
│   │
│   ├── ui/                     # 【Epic 4】Web UI 界面
│   │   ├── __init__.py
│   │   ├── app.py              # Gradio 应用入口
│   │   │
│   │   ├── components/         # UI 组件
│   │   │   ├── __init__.py
│   │   │   ├── chat.py         # 对话组件
│   │   │   ├── documents.py    # 文档管理组件
│   │   │   ├── settings.py     # 设置面板
│   │   │   ├── search.py       # 搜索组件
│   │   │   ├── model_selector.py   # 模型切换
│   │   │   ├── sync_status.py  # 同步状态显示
│   │   │   ├── citations.py    # 引用展示
│   │   │   ├── dashboard.py    # 统计仪表盘
│   │   │   └── help.py         # 帮助系统
│   │   │
│   │   ├── pages/              # 多标签页
│   │   │   ├── __init__.py
│   │   │   ├── chat_page.py
│   │   │   ├── document_page.py
│   │   │   └── admin_page.py
│   │   │
│   │   ├── theme.py            # UI 主题配置
│   │   └── assets/             # 静态资源
│   │       ├── css/
│   │       ├── js/
│   │       └── images/
│   │
│   ├── utils/                  # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py           # 日志工具
│   │   ├── text.py             # 文本处理工具
│   │   ├── time.py             # 时间工具
│   │   ├── validator.py        # 数据验证
│   │   ├── security.py         # 安全工具
│   │   └── async_utils.py      # 异步工具
│   │
│   ├── __init__.py
│   ├── main.py                 # 主程序入口
│   ├── config.py               # 配置管理
│   └── constants.py            # 常量定义
│
├── tests/                      # 测试代码
│   ├── __init__.py
│   ├── conftest.py             # pytest 配置和 fixtures
│   │
│   ├── unit/                   # 单元测试（Epic 对应）
│   │   ├── __init__.py
│   │   ├── test_llm/           # Epic 1 测试
│   │   │   ├── test_ollama.py
│   │   │   └── test_manager.py
│   │   ├── test_rag/           # Epic 3 测试
│   │   │   ├── test_retriever.py
│   │   │   ├── test_reranker.py
│   │   │   ├── test_chunker.py
│   │   │   └── test_citation.py
│   │   ├── test_auth/          # Epic 6 测试
│   │   │   ├── test_authentication.py
│   │   │   └── test_authorization.py
│   │   └── test_document_processing/  # Epic 7 测试
│   │       ├── test_parser.py
│   │       └── test_ocr.py
│   │
│   ├── integration/            # 集成测试
│   │   ├── __init__.py
│   │   ├── test_jira_integration.py     # Epic 2
│   │   ├── test_confluence_integration.py  # Epic 2
│   │   ├── test_rag_pipeline.py         # Epic 3
│   │   ├── test_mcp_server.py           # Epic 5
│   │   └── test_storage.py
│   │
│   ├── e2e/                    # 端到端测试
│   │   ├── __init__.py
│   │   ├── test_chat_flow.py
│   │   ├── test_document_upload.py
│   │   └── test_user_workflow.py
│   │
│   ├── performance/            # 性能测试（Epic 8）
│   │   ├── __init__.py
│   │   ├── test_retrieval_performance.py
│   │   └── test_llm_performance.py
│   │
│   └── fixtures/               # 测试数据
│       ├── sample_documents/
│       ├── mock_responses/
│       └── test_configs/
│
├── .env.example                # 环境变量模板
├── .gitignore                  # Git 忽略文件
├── .pre-commit-config.yaml     # Pre-commit 钩子配置
├── docker-compose.yml          # Docker Compose 配置
├── Dockerfile                  # Docker 镜像定义
├── LICENSE                     # MIT 许可证
├── README.md                   # 项目说明（本文档）
├── requirements.txt            # Python 生产依赖
├── requirements-dev.txt        # Python 开发依赖
├── pyproject.toml              # Python 项目配置
└── setup.py                    # 安装脚本
```

### 目录结构与 Epic 对应关系

| 目录 | 对应 Epic | 说明 |
|------|----------|------|
| `src/core/llm/` | Epic 1 | 本地模型集成与管理 |
| `src/core/embedding/` | Epic 1 | Embedding 模型管理 |
| `src/integrations/` | Epic 2 | 企业知识源集成（Jira/Confluence） |
| `src/core/rag/` | Epic 3, Epic 9 | RAG 检索引擎与检索优化 |
| `src/ui/` | Epic 4 | Web UI 界面 |
| `src/mcp/` | Epic 5 | MCP 协议支持 |
| `src/auth/` | Epic 6 | 多用户与权限管理 |
| `src/document_processing/` | Epic 7 | 文档处理与 OCR |
| `src/monitoring/` | Epic 8 | 性能优化与监控 |

### 设计原则

1. **模块化**: 每个 Epic 对应独立的模块，便于并行开发和维护
2. **可扩展**: 使用基类和接口，支持多种实现（如多种向量数据库）
3. **分层架构**: API → Core → Storage，职责清晰
4. **测试覆盖**: 单元测试、集成测试、E2E 测试完整覆盖

---

## 开发指南

### 开发环境设置

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/KT-BOT.git
cd KT-BOT

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装开发依赖
pip install -r requirements-dev.txt

# 4. 安装 pre-commit hooks
pre-commit install

# 5. 运行测试
pytest tests/
```

### 代码规范

我们使用以下工具保证代码质量：

```bash
# 代码格式化
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/

# 导入排序
isort src/ tests/

# 或使用 pre-commit 自动运行所有检查
pre-commit run --all-files
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行特定测试文件
pytest tests/unit/test_retriever.py

# 查看测试覆盖率
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### 添加新的数据源

#### 1. 创建 MCP Tool

在 `src/mcp/tools/` 创建新的 Tool：

```python
# src/mcp/tools/gitlab_tool.py
from mcp import Tool

class GitLabTool(Tool):
    """GitLab MCP Tool"""

    def __init__(self, config):
        self.config = config
        self.client = self._init_client()

    def _init_client(self):
        # 初始化 GitLab 客户端
        pass

    async def search_issues(self, query: str):
        """搜索 GitLab Issues"""
        # 实现搜索逻辑
        pass

    async def get_merge_requests(self, project_id: str):
        """获取合并请求"""
        # 实现获取逻辑
        pass
```

#### 2. 注册 Tool

在 `src/mcp/server.py` 中注册：

```python
from src.mcp.tools.gitlab_tool import GitLabTool

# 在 MCP Server 初始化时注册
mcp_server.register_tool("gitlab", GitLabTool(config))
```

#### 3. 添加配置

在 `src/mcp/config.json` 中添加配置：

```json
{
  "tools": {
    "gitlab": {
      "enabled": true,
      "url": "${GITLAB_URL}",
      "token": "${GITLAB_TOKEN}"
    }
  }
}
```

#### 4. 实现数据同步

在 `src/integrations/gitlab/` 创建同步逻辑：

```python
# src/integrations/gitlab/sync.py
async def sync_gitlab_issues():
    """同步 GitLab Issues"""
    # 实现同步逻辑
    pass
```

### 调试技巧

#### 启用调试日志

```bash
# 方式 1: 环境变量
export LOG_LEVEL=DEBUG
python src/main.py

# 方式 2: 命令行参数
python src/main.py --log-level DEBUG
```

#### 使用调试器

```python
# 在代码中添加断点
import pdb; pdb.set_trace()

# 或使用 ipdb（推荐）
import ipdb; ipdb.set_trace()
```

#### 查看 RAG 检索过程

```bash
# 启用 RAG 调试模式
export RAG_DEBUG=true
python src/main.py
```

---

## 部署方案

### Docker 部署（推荐）

#### 单机部署

```bash
# 1. 构建镜像
docker build -t ktbot:latest .

# 2. 运行容器
docker run -d \
  --name ktbot \
  -p 7860:7860 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  ktbot:latest
```

#### Docker Compose 部署

使用提供的 `docker-compose.yml`：

```bash
docker-compose up -d
```

服务包括：
- **ktbot**: 主应用
- **postgres**: 数据库
- **redis**: 缓存
- **elasticsearch**: 全文检索（可选）
- **qdrant**: 向量数据库（可选）

### Kubernetes 部署

提供 Helm Chart 部署：

```bash
# 1. 添加 Helm repo
helm repo add ktbot https://charts.ktbot.io
helm repo update

# 2. 安装
helm install ktbot ktbot/ktbot \
  --namespace ktbot \
  --create-namespace \
  --set ollama.host=http://ollama-service:11434 \
  --set jira.url=https://your-jira.com \
  --set jira.token=YOUR_TOKEN

# 3. 查看状态
kubectl get pods -n ktbot
```

### 生产环境配置建议

#### 1. 使用外部数据库

```env
DATABASE_URL=postgresql://user:pass@prod-db:5432/ktbot
REDIS_URL=redis://prod-redis:6379/0
```

#### 2. 启用 HTTPS

```yaml
# nginx.conf
server {
    listen 443 ssl;
    server_name ktbot.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. 配置负载均衡

```yaml
# docker-compose.yml
services:
  ktbot:
    image: ktbot:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 8G

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - ktbot
```

#### 4. 监控和告警

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ktbot'
    static_configs:
      - targets: ['ktbot:9090']
```

---

## 常见问题

### 安装和配置

#### Q1: Ollama 连接失败

**A**: 确保 Ollama 服务正在运行：

```bash
# 检查 Ollama 状态
ollama list

# 如果未运行，启动服务
ollama serve

# 测试连接
curl http://localhost:11434/api/version
```

#### Q2: Jira/Confluence 返回 401 错误

**A**: 检查以下配置：

1. API Token 是否正确
2. 邮箱地址是否匹配
3. URL 格式是否正确（需要 https://）
4. 账号是否有相应权限

测试连接：
```bash
curl -u your-email@company.com:your-api-token \
  https://your-company.atlassian.net/rest/api/3/myself
```

#### Q3: 数据库连接失败

**A**:

```bash
# 检查 PostgreSQL 是否运行
docker ps | grep postgres

# 测试数据库连接
psql -h localhost -U postgres -d ktbot

# 重新初始化数据库
python scripts/init_db.py --reset
```

### 使用问题

#### Q4: 检索结果不准确

**A**: 尝试以下优化：

1. **调整检索参数**：
```yaml
# config/retrieval.yaml
retrieval:
  retrieval_k: 30           # 增加初始检索数量
  similarity_threshold: 0.5  # 降低阈值
  hybrid_search:
    vector_weight: 0.8       # 提高语义理解权重
```

2. **使用更好的 Embedding 模型**：
```env
OLLAMA_EMBEDDING_MODEL=bge-large-zh  # 中文
# 或
OLLAMA_EMBEDDING_MODEL=nomic-embed-text  # 多语言
```

3. **启用重排序**：
```yaml
reranker:
  enabled: true
  model: "bge-reranker-large"
```

#### Q5: 响应速度慢

**A**:

1. **使用更小的模型**：
```env
OLLAMA_MODEL=qwen2.5:7b  # 而非 32b
```

2. **启用 GPU 加速**：
```bash
# 确保 CUDA 可用
nvidia-smi

# 使用 GPU 运行 Ollama
ollama serve --gpu
```

3. **增加缓存**：
```env
REDIS_CACHE_TTL=3600  # 缓存 1 小时
```

4. **优化检索数量**：
```yaml
retrieval:
  retrieval_k: 10  # 减少检索数量
  rerank_k: 3      # 减少重排序数量
```

#### Q6: 内存不足

**A**:

1. **使用更小的模型**：
```bash
ollama pull qwen2.5:7b  # 8GB RAM
# 而非
ollama pull qwen2.5:32b  # 32GB RAM
```

2. **限制并发请求**：
```env
MAX_CONCURRENT_REQUESTS=2
```

3. **清理缓存**：
```bash
# 清理向量数据库缓存
rm -rf data/vectordb/cache

# 清理 Redis 缓存
redis-cli FLUSHDB
```

### 开发问题

#### Q7: 测试失败

**A**:

```bash
# 清理测试环境
pytest --cache-clear

# 重新安装依赖
pip install -r requirements-dev.txt

# 运行特定测试
pytest tests/unit/test_retriever.py -v
```

#### Q8: Pre-commit 钩子失败

**A**:

```bash
# 更新 pre-commit hooks
pre-commit autoupdate

# 手动运行所有检查
pre-commit run --all-files

# 跳过特定检查（不推荐）
SKIP=flake8 git commit -m "message"
```

#### Q9: Docker 构建失败

**A**:

```bash
# 清理 Docker 缓存
docker system prune -a

# 使用 no-cache 重新构建
docker build --no-cache -t ktbot:latest .

# 查看构建日志
docker build -t ktbot:latest . 2>&1 | tee build.log
```

---

## 路线图

### ✅ 已完成（v0.1 + Sprint 2）

**v0.1.0 基础功能**:
- [x] Ollama 模型集成（qwen2.5:7b, bge-large-zh）
- [x] Jira/Confluence 数据同步
- [x] 基础 RAG 检索（向量检索）
- [x] Web UI 对话界面（Gradio + FastAPI）

**Sprint 2 增强功能** ⭐ 新增:
- [x] 混合检索系统（向量 + BM25 + RRF）
- [x] Cross-Encoder 重排序（bge-reranker-large）
- [x] 完整 RAG Pipeline（Hybrid → Rerank → Top-K）
- [x] 文档管理系统（后端 API + Gradio UI）
- [x] 测试覆盖率提升（60.58% 整体，核心模块 85%+）

### 🚧 进行中（v0.2 - Sprint 3-4）

- [ ] 引用溯源系统（Sprint 3）
- [ ] Embedding 模型管理（Sprint 3）
- [ ] 模型配置文件系统（Sprint 3）
- [ ] 本地文档上传（Sprint 3）
- [ ] 数据同步调度器（Sprint 4）
- [ ] Docker 部署完善（Sprint 4）

### 📋 计划中（v0.3）

- [ ] MCP 协议完整支持
- [ ] 多用户认证系统
- [ ] 权限管理
- [ ] 对话历史管理
- [ ] 高级推理能力（ReAct Agent）

### 🔮 未来展望（v1.0）

- [ ] GraphRAG 集成
- [ ] 多模态支持（图片、视频）
- [ ] 更多数据源（GitLab, Notion, etc）
- [ ] 移动端应用
- [ ] 企业级功能（SSO、审计日志）
- [ ] 性能优化（分布式部署）

---

## 贡献指南

我们欢迎任何形式的贡献！

### 如何贡献

1. **Fork 本项目**
2. **创建特性分支**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **提交更改**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **推送到分支**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **开启 Pull Request**

### 贡献类型

- 🐛 **Bug 修复** - 修复已知问题
- ✨ **新功能** - 添加新的功能
- 📝 **文档** - 改进文档
- 🎨 **UI/UX** - 改进用户界面
- ⚡️ **性能** - 性能优化
- ✅ **测试** - 添加测试用例
- 🔧 **配置** - 改进配置和部署

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 所有公共 API 必须有文档注释
- 新功能需要添加测试
- 提交信息使用约定式提交（Conventional Commits）

### 报告 Bug

使用 GitHub Issues 报告 Bug，请包含：

- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（OS、Python 版本、Ollama 版本等）
- 日志输出

### 功能请求

我们欢迎新功能建议！请通过 GitHub Issues 提交，包含：

- 功能描述
- 使用场景
- 预期效果
- 可能的实现方案

---

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

### 第三方依赖许可

- **Ollama**: MIT License
- **Gradio**: Apache 2.0 License
- **FastAPI**: MIT License
- **LangChain**: MIT License
- **Kotaemon**: Apache 2.0 License (设计参考)

---

## 致谢

### 项目灵感

- **[Kotaemon](https://github.com/Cinnamon/kotaemon)** - 提供了优秀的 RAG 系统设计参考
- **[Ollama](https://ollama.ai/)** - 使本地 LLM 部署变得简单
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - 提供标准化的扩展协议

### 开源社区

感谢以下开源项目：

- **LangChain** - RAG 框架基础
- **ChromaDB** - 向量数据库
- **Gradio** - 快速构建 Web UI
- **FastAPI** - 高性能 Web 框架
- **Atlassian Python API** - Jira/Confluence 集成

### 贡献者

感谢所有为 KT BOT 做出贡献的开发者！

<a href="https://github.com/yourusername/KT-BOT/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=yourusername/KT-BOT" />
</a>

---

## 联系我们

### 获取帮助

- 📖 **文档**: [完整文档](./docs/)
- 💬 **讨论**: [GitHub Discussions](https://github.com/yourusername/KT-BOT/discussions)
- 🐛 **Bug 报告**: [GitHub Issues](https://github.com/yourusername/KT-BOT/issues)
- 📧 **邮件**: ktbot@example.com

### 社交媒体

- **Twitter**: [@ktbot](https://twitter.com/ktbot)
- **Discord**: [加入我们的 Discord 社区](https://discord.gg/ktbot)
- **知乎**: [KT BOT 官方账号](https://www.zhihu.com/people/ktbot)

---

## 文档结构

本项目采用精简的敏捷开发文档架构，核心文档职责清晰：

| 文档 | 用途 | 更新频率 | 受众 |
|------|------|---------|------|
| **[README.md](./README.md)** | 项目概览、快速开始、使用指南 | 稳定 | 所有人 |
| **[Requirements.md](./Requirements.md)** | Epic、用户故事、验收标准、版本规划 | 频繁 | 产品/开发团队 |
| **[SPRINTS.md](./SPRINTS.md)** | Sprint 计划、任务分解、进度跟踪 | 每 Sprint | 开发团队 |
| **[CHANGELOG.md](./CHANGELOG.md)** | 已发布版本的实际变更记录 | 每次发布 | 所有人 |

### 文档关系流程

```
需求定义              任务分解               开发              交付记录
    ↓                    ↓                    ↓                    ↓
Requirements.md → SPRINTS.md → 实际开发与迭代 → CHANGELOG.md
  (做什么)            (如何做)              (开发中)            (已完成)
  包含 Epic           Sprint 任务
  用户故事            技术实现
  版本规划            进度跟踪
```

**推荐阅读顺序**:
1. **新用户**: README.md → CHANGELOG.md → Requirements.md
2. **开发人员**: README.md → Requirements.md → SPRINTS.md
3. **项目管理**: Requirements.md → SPRINTS.md → CHANGELOG.md

---

## 更新日志

详细的版本变更历史请查看 [CHANGELOG.md](./CHANGELOG.md)

### 最新进展: Sprint 2 完成 (2026-01-20)

**Sprint 2 交付** (100% 完成):
- ✅ 混合检索系统（向量 + BM25 + RRF 融合）
- ✅ Cross-Encoder 重排序（bge-reranker-large）
- ✅ 完整 RAG Pipeline（Hybrid → Rerank → Top-K）
- ✅ 文档管理系统（7个API端点 + Gradio UI）
- ✅ 测试覆盖率大幅提升（Jira: 97.28%, Confluence: 91.37%）
- ✅ 60+ 新增测试用例，~4,000行生产代码

**最新版本: v0.1.0** (2025-12-30)
- Ollama 本地模型集成
- Jira/Confluence 企业工具集成
- 基础 RAG 检索引擎（ChromaDB）
- Gradio Web UI 对话界面

**v0.2.0 进展** (Sprint 2-4):
- ✅ 混合检索和重排序（已完成）
- ✅ 文档管理（已完成）
- ⏳ 引用溯源（Sprint 3 计划）
- ⏳ 模型管理完善（Sprint 3 计划）

### 未来版本规划

完整的需求和版本规划请查看：[Requirements.md](./Requirements.md)

- **v0.2.0** (Q1 2026): 混合检索、重排序、引用溯源、Web UI 增强
- **v0.3.0** (Q2 2026): MCP 协议、多用户认证、权限管理
- **v1.0.0** (Q3 2026): GraphRAG、多模态、企业级功能

当前开发进度请查看：[SPRINTS.md](./SPRINTS.md)

---

<p align="center">
  <strong>⭐ 如果这个项目对你有帮助，请给我们一个 Star！</strong>
</p>

<p align="center">
  Made with ❤️ by KT BOT Team
</p>

<p align="center">
  <a href="#目录">回到顶部</a>
</p>
