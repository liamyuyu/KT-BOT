# KT BOT

<p align="center">
  <img src="https://img.shields.io/badge/Ollama-Powered-blue" alt="Ollama">
  <img src="https://img.shields.io/badge/MCP-Integrated-green" alt="MCP">
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License">
</p>

> 基于 Ollama 本地模型的智能问答助手，集成 Jira 和 Confluence 作为知识库，通过 MCP 协议提供企业级 AI 对话服务。

## 项目简介

- [什么是 Kotaemon](#什么是-kotaemon)
- [核心理念](#核心理念)
- [技术架构](#技术架构)
- [核心功能](#核心功能)
- [RAG 工作原理](#rag-工作原理)
- [安装部署](#安装部署)
- [配置说明](#配置说明)
- [使用场景](#使用场景)
- [与 KT BOT 的对比](#与-kt-bot-的对比)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---


KT BOT 是一个类似 [kotaemon](https://github.com/Cinnamon/kotaemon) 的智能知识库问答系统，专为企业团队设计。它利用本地部署的 Ollama 模型，结合 Model Context Protocol (MCP)，无缝连接 Jira 和 Confluence 等企业工具，为团队提供基于自有知识库的 AI 问答服务。

### 核心特性

- **本地模型部署** - 基于 Ollama，支持完全私有化部署，数据安全可控
- **企业知识库集成** - 直接连接 Jira 和 Confluence，实时获取项目信息和文档
- **MCP 协议支持** - 采用标准化的 Model Context Protocol，易于扩展
- **智能问答** - 支持自然语言提问，智能检索和总结相关信息
- **多模型支持** - 兼容 Ollama 支持的各类开源大语言模型
- **隐私保护** - 所有数据处理在本地完成，不依赖云端服务
- **界面** - 沿用kotaemon的UI界面，模型选择，对话

## 技术架构

```
┌─────────────────┐
│   用户界面      │
└────────┬────────┘
         │
┌────────▼────────┐
│   KT BOT 核心   │
└────────┬────────┘
         │
    ┌────┴────┐
    │   MCP   │
    └────┬────┘
         │
    ┌────┴───────────────────┐
    │                        │
┌───▼────┐           ┌──────▼──────┐
│ Ollama │           │  数据源     │
│ 模型   │           │ Jira/       │
└────────┘           │ Confluence  │
                     └─────────────┘
```

## 系统要求

- **操作系统**: macOS, Linux, Windows (WSL2)
- **Python**: 3.9+
- **Ollama**: 最新版本
- **内存**: 建议 8GB+ (取决于模型大小)
- **存储**: 10GB+ (用于模型存储)

## 快速开始

### 1. 安装 Ollama

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# 拉取推荐模型
ollama pull llama3.1
# 或者使用其他模型
ollama pull qwen2.5
```

### 2. 克隆项目

```bash
git clone https://github.com/your-username/KT-BOT.git
cd KT-BOT
```

### 3. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 配置环境变量

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下参数：

```env
# Ollama 配置
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Jira 配置
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# Confluence 配置
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token

# MCP 配置
MCP_SERVER_PORT=3000
```

### 5. 启动服务

```bash
# 启动 MCP 服务器
python src/mcp_server.py

# 启动 KT BOT（新终端）
python src/main.py
```

## 配置说明

### Jira API Token 获取

1. 登录 Atlassian 账号
2. 访问 [API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
3. 点击 "Create API token"
4. 复制 token 并保存到 `.env` 文件

### Confluence API Token 获取

使用与 Jira 相同的 API Token 即可。

### 模型选择

KT BOT 支持 Ollama 的所有模型，推荐配置：

| 模型 | 内存需求 | 特点 |
|------|---------|------|
| llama3.1:8b | 8GB | 平衡性能，中文支持良好 |
| qwen2.5:7b | 8GB | 中文优化，推理速度快 |
| llama3.1:70b | 40GB | 高性能，需要大内存 |
| mistral:7b | 8GB | 速度快，英文优秀 |

## 使用指南

### 基本问答

```
用户: 最近有哪些高优先级的 bug？
KT BOT: 根据 Jira 数据，当前有 3 个高优先级 bug...

用户: 关于用户认证的文档在哪？
KT BOT: 在 Confluence 中找到以下相关文档...
```

### 高级功能

- **多轮对话** - 支持上下文关联的连续提问
- **跨平台检索** - 同时搜索 Jira 和 Confluence
- **智能总结** - 自动提取和总结关键信息
- **引用溯源** - 提供信息来源链接

## MCP 服务器配置

### 添加自定义数据源

编辑 `src/mcp_config.json`：

```json
{
  "servers": {
    "jira": {
      "enabled": true,
      "type": "jira",
      "config": {}
    },
    "confluence": {
      "enabled": true,
      "type": "confluence",
      "config": {}
    },
    "custom_source": {
      "enabled": false,
      "type": "custom",
      "config": {
        "url": "https://api.example.com",
        "auth": "bearer"
      }
    }
  }
}
```

### 扩展 MCP 功能

```python
# src/mcp_extensions/custom_tool.py
from mcp import Tool

class CustomTool(Tool):
    def execute(self, params):
        # 实现自定义逻辑
        pass
```

## 项目结构

```
KT-BOT/
├── src/
│   ├── main.py              # 主程序入口
│   ├── mcp_server.py        # MCP 服务器
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑
│   │   ├── jira_service.py
│   │   ├── confluence_service.py
│   │   └── ollama_service.py
│   ├── mcp_extensions/      # MCP 扩展
│   └── utils/               # 工具函数
├── tests/                   # 测试文件
├── docs/                    # 文档
├── .env.example             # 环境变量模板
├── requirements.txt         # Python 依赖
├── README.md
└── LICENSE
```

## 开发指南

### 本地开发

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/

# 代码格式化
black src/
flake8 src/

# 类型检查
mypy src/
```

### 调试模式

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python src/main.py
```

## 常见问题

### Q: Ollama 连接失败怎么办？

A: 确保 Ollama 服务已启动：
```bash
ollama serve
```

### Q: Jira/Confluence API 返回 401 错误？

A: 检查以下配置：
- API Token 是否正确
- 邮箱是否匹配
- URL 是否正确（注意 https）

### Q: 模型响应很慢怎么办？

A: 尝试以下方法：
- 使用更小的模型（如 7B 而非 70B）
- 增加系统内存
- 使用 GPU 加速（需要支持 CUDA 的显卡）

### Q: 如何更新模型？

```bash
ollama pull <model-name>
```

### Q: 支持哪些语言？

KT BOT 支持中英文对话，模型的语言能力取决于所选的 Ollama 模型。

## 路线图

- [ ] Web UI 界面
- [ ] 更多数据源支持（GitLab, Notion, etc）
- [ ] 向量数据库集成
- [ ] 多用户权限管理
- [ ] Docker 一键部署
- [ ] RAG 优化
- [ ] 流式响应支持

## 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

- [Ollama](https://ollama.ai/) - 本地模型运行框架
- [kotaemon](https://github.com/Cinnamon/kotaemon) - 设计灵感来源
- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 协议支持

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至: your-email@example.com
- 加入讨论群: [链接]

---

⭐ 如果这个项目对你有帮助，请给我们一个 Star！
