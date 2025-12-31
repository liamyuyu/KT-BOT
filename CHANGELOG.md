# CHANGELOG / 更新日志

## [Unreleased] / [未发布]

### Planned Features / 计划功能

#### Epic 1: Local Model Integration / 本地模型集成
- Multi-model management and switching / 多模型管理与切换
- Embedding model management / Embedding 模型管理
- GPU acceleration support / GPU 加速支持
- Intelligent model recommendation / 智能模型推荐
- Model version management / 模型版本管理
- Model health check and failover / 模型健康检查与故障恢复

#### Epic 2: Enterprise Knowledge Source Integration / 企业知识源集成
- Jira connection and data sync / Jira 连接与数据同步
- Confluence connection and data sync / Confluence 连接与数据同步
- Incremental sync mechanism / 增量同步机制
- Permission inheritance / 权限继承

#### Epic 3: RAG Retrieval Engine / RAG 检索引擎
- Document indexing and chunking / 文档索引与分块
- Vector database configuration (ChromaDB/Qdrant/Milvus) / 向量数据库配置
- Hybrid retrieval (Vector + BM25) / 混合检索（向量 + 全文）
- Re-ranking with Cross-Encoder / 重排序优化
- Citation tracking / 引用溯源
- Incremental index updates / 增量索引更新
- Result filtering / 结果过滤
- Batch processing / 批量处理
- Retrieval visualization / 检索可视化

#### Epic 4: Web UI Interface / Web UI 界面
- Chat interface with Kotaemon-style design / Kotaemon 风格对话界面
- Document management / 文档管理
- Local document upload / 本地文档上传
- Settings panel / 设置面板
- Search functionality / 搜索功能
- Model switching / 模型切换
- Sync status display / 同步状态显示
- Citation display / 引用展示
- User experience optimization / 用户体验优化
- Help system / 帮助系统
- Statistics dashboard / 统计仪表盘
- Bookmark and annotation / 收藏与批注
- Multi-tab support / 多标签页支持
- Voice interaction / 语音交互

#### Epic 5: MCP Protocol Support / MCP 协议支持
- MCP server implementation / MCP 服务器实现
- Jira MCP tool / Jira MCP 工具
- Confluence MCP tool / Confluence MCP 工具
- Custom tool development framework / 自定义工具开发框架

#### Epic 6: Multi-user and Permission Management / 多用户与权限管理
- User authentication / 用户认证
- Role-based access control / 基于角色的访问控制
- Usage quota management / 使用配额管理

#### Epic 7: Document Processing and OCR / 文档处理与 OCR
- Advanced document parsing / 高级文档解析
- OCR for scanned documents / 扫描文档 OCR
- Table extraction / 表格提取
- Image recognition / 图片识别

#### Epic 8: Performance Optimization and Monitoring / 性能优化与监控
- Caching strategy / 缓存策略
- Performance monitoring / 性能监控
- Alert system / 告警系统
- Distributed deployment / 分布式部署

#### Epic 9: Retrieval Strategy Optimization / 检索策略优化
- Advanced chunking strategies / 高级分块策略
- Query expansion / 查询扩展
- Retrieval parameter tuning / 检索参数调优

---

## [0.1.0] - 2025-12-30

### Added / 新增

#### Core Features / 核心功能
- **Ollama Integration** / **Ollama 集成**
  - Local LLM deployment with Ollama / 基于 Ollama 的本地大语言模型部署
  - Support for multiple models (qwen2.5, llama3.1, etc.) / 支持多种模型（qwen2.5、llama3.1 等）
  - Embedding model support (bge-large-zh, nomic-embed-text, etc.) / Embedding 模型支持（bge-large-zh、nomic-embed-text 等）

- **Enterprise Tool Integration** / **企业工具集成**
  - Jira API integration / Jira API 集成
  - Confluence API integration / Confluence API 集成
  - Basic data synchronization / 基础数据同步

- **RAG Engine** / **RAG 引擎**
  - Basic document indexing / 基础文档索引
  - Vector storage with ChromaDB / 基于 ChromaDB 的向量存储
  - Basic semantic retrieval / 基础语义检索
  - Document chunking / 文档分块

- **Web Interface** / **Web 界面**
  - Simple chat interface / 简单对话界面
  - Basic conversation history / 基础对话历史
  - Model selection dropdown / 模型选择下拉菜单

#### Configuration / 配置
- Environment variable configuration (.env) / 环境变量配置 (.env)
- YAML-based configuration files / 基于 YAML 的配置文件
  - `config/logging.yaml` - Logging configuration / 日志配置
  - `config/retrieval.yaml` - Retrieval parameters / 检索参数
  - `config/models.yaml` - Model configuration / 模型配置

#### Deployment / 部署
- Docker support / Docker 支持
- Docker Compose deployment / Docker Compose 部署
- PostgreSQL database / PostgreSQL 数据库
- Redis caching / Redis 缓存

#### Documentation / 文档
- Comprehensive README.md / 完整的 README.md
- Requirements document (Requirements.md) / 需求文档 (Requirements.md)
- Kotaemon reference document (Kotaemon.md) / Kotaemon 参考文档 (Kotaemon.md)
- Installation and configuration guide / 安装与配置指南
- Quick start guide / 快速开始指南

#### Project Structure / 项目结构
- Modular architecture / 模块化架构
- Separation of concerns (API, Core, Integrations, MCP, UI) / 关注点分离（API、核心、集成、MCP、UI）
- Test framework setup / 测试框架配置
- CI/CD pipeline setup / CI/CD 流程配置

### Changed / 变更
- N/A (Initial Release) / 无（初始版本）

### Deprecated / 弃用
- N/A (Initial Release) / 无（初始版本）

### Removed / 移除
- N/A (Initial Release) / 无（初始版本）

### Fixed / 修复
- N/A (Initial Release) / 无（初始版本）

### Security / 安全
- API Token encryption / API Token 加密
- Environment variable protection / 环境变量保护
- Private deployment support / 私有化部署支持

### Known Issues / 已知问题

#### UI / 界面
- Limited UI functionality / 界面功能有限
- No real-time sync status display / 缺少实时同步状态显示
- Basic styling only / 仅基础样式

#### Performance / 性能
- Re-ranking not yet optimized / 重排序功能待优化
- No caching for repeated queries / 重复查询无缓存
- Limited concurrent request handling / 并发请求处理能力有限

#### Features / 功能
- No multi-user support / 不支持多用户
- No permission management / 无权限管理
- Limited document format support / 文档格式支持有限
- No OCR capability / 无 OCR 能力

#### Edge Cases / 边界情况
- Some edge cases not handled / 部分边界情况未处理
- Error handling needs improvement / 错误处理需要改进

---

## Release Notes / 发布说明

### v0.1.0 - Initial Release / 初始版本 (2025-12-30)

This is the first public release of KT BOT, an enterprise-grade intelligent knowledge base Q&A system powered by local Ollama models. The system integrates with Jira and Confluence to provide private AI-powered question answering based on your organization's knowledge base.

这是 KT BOT 的第一个公开版本，一个基于本地 Ollama 模型的企业级智能知识库问答系统。系统集成 Jira 和 Confluence，基于企业自有知识库提供私有化的 AI 问答服务。

#### What's Included / 包含内容

1. **Complete Local Deployment** / **完整本地部署**
   - All AI processing happens locally / 所有 AI 处理都在本地完成
   - No data leaves your environment / 数据不离开企业环境
   - GDPR and compliance-friendly / 符合 GDPR 和合规要求

2. **Enterprise Integration** / **企业集成**
   - Connect to Jira for issue tracking / 连接 Jira 进行问题追踪
   - Sync with Confluence for documentation / 同步 Confluence 文档
   - Real-time data access / 实时数据访问

3. **Intelligent RAG Retrieval** / **智能 RAG 检索**
   - Semantic understanding with embeddings / 基于嵌入的语义理解
   - Document chunking and indexing / 文档分块与索引
   - Context-aware responses / 上下文感知响应

4. **Simple Web Interface** / **简洁 Web 界面**
   - ChatGPT-style conversation / ChatGPT 风格对话
   - Easy model switching / 轻松切换模型
   - Conversation history / 对话历史

#### Getting Started / 快速开始

```bash
# Install Ollama / 安装 Ollama
brew install ollama  # macOS

# Clone the repository / 克隆仓库
git clone https://github.com/yourusername/KT-BOT.git
cd KT-BOT

# Install dependencies / 安装依赖
pip install -r requirements.txt

# Configure environment / 配置环境
cp .env.example .env
# Edit .env with your settings / 编辑 .env 填入配置

# Start the application / 启动应用
python src/main.py
```

For detailed installation instructions, see [README.md](README.md).
详细安装说明请参见 [README.md](README.md)。

#### System Requirements / 系统要求

**Minimum / 最低配置:**
- CPU: 4 cores / 4 核
- RAM: 8GB
- Storage: 20GB / 存储: 20GB

**Recommended / 推荐配置:**
- CPU: 8+ cores / 8+ 核
- RAM: 16GB+
- Storage: 50GB+ SSD / 存储: 50GB+ SSD
- GPU: CUDA-compatible (optional) / GPU: 支持 CUDA（可选）

#### Supported Models / 支持的模型

**Chat Models / 对话模型:**
- qwen2.5:7b, qwen2.5:14b, qwen2.5:32b (Chinese optimized / 中文优化)
- llama3.1:8b, llama3.1:70b (English / 英文)
- mistral:7b (Fast response / 快速响应)

**Embedding Models / 嵌入模型:**
- bge-large-zh (Chinese / 中文) - Recommended / 推荐
- nomic-embed-text (Multilingual / 多语言)
- mxbai-embed-large (English / 英文)

#### Feedback and Support / 反馈与支持

- **Documentation** / **文档**: [Full Documentation](./docs/)
- **Issues** / **问题**: [GitHub Issues](https://github.com/yourusername/KT-BOT/issues)
- **Discussions** / **讨论**: [GitHub Discussions](https://github.com/yourusername/KT-BOT/discussions)

---

## Roadmap / 路线图

### v0.2 (Q1 2026)
- Enhanced Web UI / 增强 Web UI
- Hybrid retrieval (Vector + BM25) / 混合检索（向量 + 全文）
- Re-ranking system / 重排序系统
- Citation tracking / 引用溯源
- Docker deployment improvements / Docker 部署改进

### v0.3 (Q2 2026)
- Full MCP protocol support / 完整 MCP 协议支持
- Multi-user authentication / 多用户认证
- Permission management / 权限管理
- Conversation history management / 对话历史管理
- Advanced reasoning (ReAct Agent) / 高级推理能力（ReAct Agent）

### v1.0 (Q3 2026)
- GraphRAG integration / GraphRAG 集成
- Multimodal support (images, videos) / 多模态支持（图片、视频）
- More data sources (GitLab, Notion, etc.) / 更多数据源（GitLab、Notion 等）
- Mobile application / 移动端应用
- Enterprise features (SSO, audit logs) / 企业级功能（SSO、审计日志）
- Performance optimization (distributed deployment) / 性能优化（分布式部署）

---

## How to Upgrade / 如何升级

### From v0.1.x to v0.2.x (Future) / 从 v0.1.x 升级到 v0.2.x（未来）

```bash
# Pull latest code / 拉取最新代码
git pull origin main

# Update dependencies / 更新依赖
pip install -r requirements.txt --upgrade

# Run database migrations / 运行数据库迁移
python scripts/migrate_db.py

# Restart services / 重启服务
docker-compose restart
```

---

## Versioning / 版本控制

This project follows [Semantic Versioning](https://semver.org/):
本项目遵循[语义化版本控制](https://semver.org/)：

- **MAJOR** version for incompatible API changes / 重大版本：不兼容的 API 变更
- **MINOR** version for new functionality in a backward-compatible manner / 次要版本：向后兼容的新功能
- **PATCH** version for backward-compatible bug fixes / 补丁版本：向后兼容的问题修复

---

## Contributing / 贡献

We welcome contributions! Please see [README.md](README.md#贡献指南) for guidelines.
我们欢迎贡献！请参阅 [README.md](README.md#贡献指南) 了解指南。

---

## License / 许可证

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

**Generated with** ❤️ **by KT BOT Team**
**由 KT BOT 团队用** ❤️ **制作**

[Unreleased]: https://github.com/yourusername/KT-BOT/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/KT-BOT/releases/tag/v0.1.0
