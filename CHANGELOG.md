# CHANGELOG / 更新日志

All notable changes to this project will be documented in this file.
本文档记录项目的所有重要变更。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)。

---

## [Unreleased] / [未发布]

> 对应 **Sprint 1** 进行中的任务，详见 [SPRINTS.md](./SPRINTS.md)

### Added / 新增

#### 2026-01-03 - Sprint 1 Task 1.1: LLM Module Implementation ✅

**Epic 1: 本地模型集成与管理**
- ✅ **LLM 基础架构** (Story 1.1)
  - 实现 `BaseLLM` 和 `BaseEmbedding` 抽象基类
  - 支持异步 generate、chat、embed 等核心接口
  - 完整的流式和非流式生成支持

- ✅ **Ollama 集成** (Story 1.1, 1.2)
  - `OllamaLLM`: 完整的 Ollama LLM 客户端实现
  - `OllamaEmbedding`: Embedding 模型支持
  - 支持 qwen2.5:7b、llama3.1:8b 等多个模型
  - 异步 HTTP 客户端（httpx），支持超时和错误处理

- ✅ **模型管理器** (Story 1.2)
  - `LLMManager`: 统一的模型生命周期管理
  - 模型实例缓存机制，提升性能
  - 支持多模型并存和动态切换
  - 全局单例模式 `get_llm_manager()`

- ✅ **健康检查系统** (Story 1.9)
  - `LLMHealthChecker`: 全面的健康监控
  - Ollama 服务状态检查
  - 模型可用性验证
  - 详细的健康状态报告（healthy/degraded/unhealthy）

- ✅ **测试与示例**
  - 33 个单元测试（Manager: 18, Ollama: 15）
  - 交互式示例脚本 `examples/test_llm.py`
  - 完整的测试覆盖（生成、聊天、流式、健康检查）

- ✅ **文档**
  - 详细的 API 文档和使用示例
  - Sprint 1 Task 1.1 完成总结
  - Docker 部署指南（macOS 12 workaround）

**技术栈**
- httpx 0.28.1 - 异步 HTTP 客户端
- pydantic 2.12.5 - 数据验证和配置管理
- Python 3.10+ with async/await

**代码统计**
- 生产代码: ~1,216 行
- 测试代码: ~443 行
- 总计: ~1,879 行（10 个文件）

#### 2026-01-05 - Sprint 1 Task 1.3: Jira API Integration ✅

**Epic 2: 企业知识源集成**
- ✅ **Jira API 客户端** (Story 2.1)
  - `JiraClient`: 完整的 Jira API 客户端实现
  - 支持 Issue 查询、分页、JQL 查询
  - 健康检查和连接状态监控
  - 自动重试机制（使用 tenacity）

- ✅ **数据模型** (Story 2.1)
  - `JiraIssue`: 完整的 Issue 数据模型
  - `JiraUser`, `JiraProject`, `JiraComment`, `JiraAttachment` 等关联模型
  - Pydantic 数据验证和序列化
  - 支持完整的 Issue 字段（状态、类型、优先级、评论、附件等）

- ✅ **错误处理** (Story 2.1)
  - 自定义异常类（认证失败、连接错误、API 错误、资源未找到、限流）
  - 自动重试机制（指数退避策略）
  - 详细的错误日志和诊断信息

- ✅ **配置管理** (Story 2.1)
  - Jira 连接配置（URL、邮箱、API Token）
  - 支持环境变量配置
  - 可配置的超时和请求限制

- ✅ **测试与示例** (Story 2.1)
  - 17 个单元测试（连接、健康检查、Issue 查询、错误处理）
  - 集成测试框架（需要真实 Jira 凭据）
  - 交互式示例脚本 `examples/test_jira.py`
  - 测试覆盖率 > 70%

- ✅ **文档**
  - 详细的 API 文档和使用示例
  - 配置指南（如何获取 API Token）
  - 错误处理最佳实践

**技术栈**
- jira 3.6.0+ - Jira Python SDK
- atlassian-python-api 3.41.0+ - Atlassian API 客户端
- tenacity 8.2.3+ - 重试机制
- pydantic 2.5.0+ - 数据验证

**代码统计**
- 生产代码: ~600 行 (client.py: 430, models.py: 130, exceptions.py: 40)
- 测试代码: ~550 行 (单元测试: 450, 集成测试: 100)
- 示例代码: ~250 行 (examples/test_jira.py)
- 总计: ~1,400 行（6 个文件）

**功能亮点**
- 完全支持 Jira Cloud 和 Server
- 支持分页查询（处理大量 Issue）
- 支持自定义 JQL 查询
- 自动解析复杂的 Issue 数据结构
- 全局单例模式，避免重复连接
- 上下文管理器支持（自动关闭连接）

### Planned / 计划中

#### v0.1.1 - ✅ Sprint 1-3 阶段完成（计划于 Sprint 3: 2026-01-20 ~ 2026-02-02）

**模型管理增强**
- [ ] Embedding 模型独立管理（Story 1.4）- 支持多种 Embedding 模型，独立配置，多语言支持
- [ ] models.yaml 配置文件管理（Story 1.5）- 统一模型配置，热更新，参数管理
- [ ] 模型健康检查系统（Story 1.9）- 自动健康检查，测试用例，自动修复机制

**RAG 引擎增强**
- [ ] 引用溯源系统（Story 3.5）- 引用来源展示，引用链追踪，点击跳转原文

**文档管理**
- [ ] 本地文档上传功能（Story 4.13）- 拖拽上传，多格式支持（PDF/Word/Markdown/TXT），自动索引

**开发环境**
- [ ] CI/CD 流程完善 - 自动化测试，代码覆盖率报告（>80%），自动化部署

**交付目标**：完成 Requirements.md Sprint 1-3 阶段的所有剩余任务

#### v0.2.0 - Enhanced Retrieval（计划于 Sprint 2: 进行中）

**RAG 检索增强**
- [ ] 混合检索实现（Story 3.3）- BM25 全文检索 + 向量检索融合（RRF 算法）
- [ ] Cross-Encoder 重排序（Story 3.4）- 使用 bge-reranker-large 提升检索准确率

**Web UI**
- [ ] 文档管理面板（Story 4.2）- 文档列表，上传/删除，元数据展示，搜索过滤

### Changed / 变更
- None / 无

### Fixed / 修复
- None / 无

---

## [0.1.0] - 2025-12-30 ✅

> **MVP 发布** - 完成 Sprint 1（对应 Requirements.md Sprint 1-3 阶段的部分任务）

### Added / 新增

**核心功能**
- Ollama 集成 - 本地 LLM 部署，支持 qwen2.5、llama3.1 等多模型
- Jira/Confluence 集成 - API 集成和基础数据同步
- RAG 引擎 - ChromaDB 向量存储，基础文档索引和语义检索
- Web 界面 - 简单对话界面，对话历史，模型选择

**基础架构**
- Docker Compose 部署
- PostgreSQL 数据库 + Redis 缓存
- YAML 配置文件（logging, retrieval, models）
- 模块化架构（API/Core/Integrations/MCP/UI）

**文档**
- 完整的 README.md、Requirements.md、SPRINTS.md
- 安装配置指南和快速开始指南

### Security / 安全
- API Token 加密，环境变量保护，私有化部署支持

### Known Issues / 已知问题
- UI 功能有限，需要增强（计划于 Sprint 2-3）
- 重排序功能待优化（计划于 Sprint 2）
- 不支持多用户和权限管理（计划于后续 Sprint）

---

## 相关文档 / Related Documents

- [需求文档 Requirements.md](./Requirements.md) - Epic、用户故事、验收标准
- [Sprint 规划 SPRINTS.md](./SPRINTS.md) - Sprint 计划、任务分解、进度跟踪

---

[Unreleased]: https://github.com/yourusername/KT-BOT/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/KT-BOT/releases/tag/v0.1.0
