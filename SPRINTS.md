# Sprint Planning / Sprint 规划

## 文档说明

本文档用于跟踪 Sprint 迭代、任务分解和执行进度。

- **Sprint 周期**: 2周
- **团队容量**: 根据实际团队规模调整
- **更新频率**: 每个 Sprint 开始和结束时更新

---

## Requirements.md Sprint 阶段映射 / Requirements Sprint Phase Mapping

> **说明**: Requirements.md 中定义的 Sprint 阶段是长期规划（3-5周），而本文档中的 Sprint 是 2 周敏捷迭代。以下是两者的映射关系：

### Phase 1: ✅ Sprint 1-3 - 基础设施与模型管理（3周）

**Requirements.md 定义的目标**: 搭建基础架构，完成核心模型管理功能

**包含的用户故事**:
- [x] Story 1.1: Ollama 模型初始化 (5点) - 已完成于实际 Sprint 1
- [x] Story 1.2: 多模型管理 (8点) - 已完成于实际 Sprint 1
- [ ] Story 1.4: Embedding 模型管理 (8点) - 计划于 Sprint 3
- [ ] Story 1.5: 模型配置文件管理 (5点) - 计划于 Sprint 3
- [ ] Story 1.9: 模型健康检查 (5点) - 计划于 Sprint 3
- [x] Story 4.1: 基础对话界面 (8点) - 已完成于实际 Sprint 1
- [x] 基础架构搭建（Docker、数据库）- 已完成
- [ ] 开发环境配置和 CI/CD - 进行中

**实际 Sprint 映射**: Sprint 1 (已完成) + Sprint 3 (计划中)

**交付物状态**:
- [x] 完整的 Ollama 模型管理系统（对话模型）
- [ ] Embedding 模型独立管理系统
- [ ] 模型健康检查机制
- [x] 基础对话界面原型
- [ ] 完整的开发文档和 CI/CD

---

### Phase 1: Sprint 4-7 - 数据集成与模型优化（4周）

**Requirements.md 定义的目标**: 完成 Jira 和 Confluence 集成，优化模型性能，扩展文档来源

**包含的用户故事**:
- [x] Story 2.1: Jira API 集成 (8点) - 已完成于实际 Sprint 1
- [x] Story 2.2: Confluence API 集成 (8点) - 已完成于实际 Sprint 1
- [ ] Story 2.3: 数据同步调度器 (5点) - 计划于 Sprint 4
- [ ] Story 4.13: 本地文档上传 (8点) - 计划于 Sprint 3
- [ ] Story 1.6: GPU 加速配置 (8点) - 计划于 Sprint 4
- [ ] Story 1.7: 智能模型推荐系统 (5点) - 计划于 Sprint 4
- [ ] Story 4.2: 文档管理界面 (8点) - 进行中于实际 Sprint 2

**实际 Sprint 映射**: Sprint 1 (已完成) + Sprint 2-4 (进行中/计划中)

**交付物状态**:
- [x] 自动同步 Jira/Confluence 数据
- [ ] 本地文档上传和管理
- [ ] 文档列表和管理功能
- [ ] GPU 加速支持（可选）
- [ ] 智能模型推荐功能
- [ ] 同步日志和错误处理

---

### Phase 1: Sprint 8-12 - RAG 引擎核心与基础 UI（5周）

**Requirements.md 定义的目标**: 实现完整的 RAG 检索系统和核心 UI 功能

**包含的用户故事**:
- [x] Story 3.2: 向量数据库配置（ChromaDB） (8点) - 已完成于实际 Sprint 1
- [x] Story 3.1: 基础文档索引 (13点) - 已完成于实际 Sprint 1
- [ ] Story 3.3: 混合检索（向量 + BM25） (13点) - 进行中于实际 Sprint 2
- [ ] Story 3.4: Cross-Encoder 重排序 (8点) - 进行中于实际 Sprint 2
- [ ] Story 3.5: 引用溯源系统 (8点) - 计划于 Sprint 3
- [ ] Story 3.6: 增量索引更新 (8点) - 计划于 Sprint 3
- [ ] Story 3.7: 检索结果过滤 (5点) - 计划于 Sprint 4
- [ ] Story 3.10: 批量索引与异步处理 (8点) - 计划于 Sprint 5
- [ ] Story 9.1: 智能 Chunking (8点) - 计划于 Sprint 5

**实际 Sprint 映射**: Sprint 1-5

**交付物状态**:
- [x] 基础向量数据库配置（ChromaDB）
- [ ] 完整的混合检索流程
- [ ] Cross-Encoder 重排序
- [ ] 引用溯源和展示
- [ ] 增量索引机制
- [ ] 批量处理系统

---

## 当前 Sprint / Current Sprint

### Sprint 2 (2026-01-06 ~ 2026-01-19)

**Sprint 目标**: 完成 Epic 3 的混合检索和重排序功能，增强 Web UI 基础交互

**包含的用户故事**:
- [ ] Story 3.3: 混合检索（向量 + BM25） - Epic 3 (13点)
- [ ] Story 3.4: Cross-Encoder 重排序 - Epic 3 (8点)
- [ ] Story 4.2: 文档管理面板 - Epic 4 (8点)

**总故事点数**: 29 点

#### Task 2.1: 实现 BM25 全文检索

**来源**: Story 3.3
**负责人**: TBD
**优先级**: P0
**预估工作量**: 3 天
**依赖**: Epic 3 基础文档索引已完成

**子任务**:
- [ ] 安装和配置 Rank-BM25 库
- [ ] 实现 BM25 索引构建
- [ ] 实现 BM25 检索接口
- [ ] 添加分词器支持（中英文）
- [ ] 编写单元测试（覆盖率 > 80%）
- [ ] 性能测试：10000 文档检索 < 100ms

**技术要点**:
```python
# src/rag/retrievers/bm25_retriever.py
from rank_bm25 import BM25Okapi
```

---

#### Task 2.2: 实现混合检索融合策略

**来源**: Story 3.3
**负责人**: TBD
**优先级**: P0
**预估工作量**: 4 天
**依赖**: Task 2.1

**子任务**:
- [ ] 设计 Reciprocal Rank Fusion (RRF) 算法
- [ ] 实现向量检索 + BM25 结果合并
- [ ] 添加可配置权重参数
- [ ] 实现结果去重逻辑
- [ ] 添加检索结果评分归一化
- [ ] 集成测试：对比单一检索 vs 混合检索效果
- [ ] 更新配置文件 `config/retrieval.yaml`

**验收标准**:
- 混合检索准确率提升 > 15%（相比纯向量检索）
- 支持动态调整向量/BM25 权重

---

#### Task 2.3: 集成 Cross-Encoder 重排序

**来源**: Story 3.4
**负责人**: TBD
**优先级**: P1
**预估工作量**: 3 天
**依赖**: Task 2.2

**子任务**:
- [ ] 选择 Cross-Encoder 模型（bge-reranker-large）
- [ ] 实现模型加载和推理
- [ ] 实现 Top-K 重排序逻辑
- [ ] 添加批处理支持（减少推理次数）
- [ ] 性能优化：缓存重排序结果
- [ ] 编写性能基准测试
- [ ] 更新 `config/models.yaml`

**技术要点**:
```python
# 使用 sentence-transformers 的 CrossEncoder
from sentence_transformers import CrossEncoder
model = CrossEncoder('BAAI/bge-reranker-large')
```

---

#### Task 2.4: Web UI 文档管理面板

**来源**: Story 4.2
**负责人**: TBD
**优先级**: P1
**预估工作量**: 4 天
**依赖**: 无

**子任务**:
- [ ] 设计文档列表 UI（Gradio Dataframe）
- [ ] 实现文档上传接口
- [ ] 实现文档删除功能
- [ ] 显示文档元数据（来源、大小、索引状态）
- [ ] 添加文档搜索过滤功能
- [ ] 实现文档预览功能
- [ ] 编写 E2E 测试

**UI 设计参考**: Kotaemon 文档管理界面

---

### Sprint 验收标准

**功能验收**:
- [ ] 所有用户故事的验收标准通过
- [ ] 混合检索功能在测试环境运行正常
- [ ] 重排序提升检索准确率 > 10%
- [ ] 文档管理面板 UI 完成并可用

**技术验收**:
- [ ] 代码覆盖率 > 80%
- [ ] 所有单元测试和集成测试通过
- [ ] 代码 Review 通过（无 P0/P1 问题）
- [ ] API 文档更新
- [ ] 配置文件更新

**性能验收**:
- [ ] 混合检索延迟 < 500ms（1000 文档库）
- [ ] 重排序延迟 < 200ms（Top-20 候选）
- [ ] 系统内存占用 < 8GB

---

## 已完成 Sprint / Completed Sprints

### Sprint 1 ✅ (2025-12-16 ~ 2025-12-30) 

**Sprint 目标**: 完成 v0.1.0 MVP 发布 - 基础功能上线

**已完成的用户故事**:
- [x] Story 1.1: Ollama 模型初始化 (5点)
- [x] Story 1.2: 多模型管理 (8点)
- [x] Story 2.1: Jira API 集成 (8点)
- [x] Story 2.2: Confluence API 集成 (8点)
- [x] Story 3.1: 基础文档索引 (13点)
- [x] Story 3.2: 向量数据库配置（ChromaDB） (8点)
- [x] Story 4.1: 简单对话界面 (5点)

**总故事点数**: 55 点

**主要成果**:
- ✅ Ollama 本地模型集成完成
- ✅ Jira/Confluence 基础数据同步实现
- ✅ RAG 基础检索引擎上线
- ✅ Web UI 对话界面可用
- ✅ Docker 部署环境配置完成
- ✅ 发布 v0.1.0 版本

**技术亮点**:
- ChromaDB 向量数据库选型
- Gradio 快速 UI 原型开发
- Docker Compose 一键部署

**遇到的问题**:
- 中文分词效果需优化
- 向量检索准确率待提升（需要混合检索）
- UI 功能较简陋（需要增强）

**改进计划**:
- Sprint 2 实现混合检索
- Sprint 3 增强 UI 交互

---

## 计划中的 Sprint / Upcoming Sprints

### Sprint 3 (2026-01-20 ~ 2026-02-02)

**计划目标**: 完成 Sprint 1-3 剩余任务（模型管理完善）+ 引用溯源 + 本地文档上传

**计划用户故事**:
- [ ] Story 1.4: Embedding 模型管理 - Epic 1 (8点) ⭐ Sprint 1-3 补充
- [ ] Story 1.5: 模型配置文件管理 - Epic 1 (5点) ⭐ Sprint 1-3 补充
- [ ] Story 1.9: 模型健康检查 - Epic 1 (5点) ⭐ Sprint 1-3 补充
- [ ] Story 3.5: 引用溯源系统 - Epic 3 (8点)
- [ ] Story 4.13: 本地文档上传 - Epic 4 (8点)

**预估故事点数**: 34 点

**技术准备**:
- 完善 Embedding 模型独立配置
- 设计 models.yaml 配置结构
- 实现模型健康检查机制
- 研究引用链追踪方案
- 调研文件上传最佳实践

---

#### Task 3.1: Embedding 模型独立管理

**来源**: Story 1.4
**负责人**: TBD
**优先级**: P0
**预估工作量**: 3 天
**依赖**: 无

**子任务**:
- [ ] 实现 Embedding 模型独立配置（与对话模型分离）
- [ ] 添加 Embedding 模型下载和验证（bge-large-zh, nomic-embed-text, mxbai-embed-large）
- [ ] 实现 Embedding 模型预加载和缓存
- [ ] 添加多语言 Embedding 支持（中文/英文/多语言）
- [ ] 开发 Embedding 质量测试工具
- [ ] 显示 Embedding 模型的维度和语言支持信息
- [ ] 编写单元测试

**技术要点**:
```python
# config/models.yaml
embedding_models:
  default: bge-large-zh
  options:
    - name: bge-large-zh
      dimension: 1024
      language: zh
    - name: nomic-embed-text
      dimension: 768
      language: multilingual
```

**验收标准**:
- Embedding 模型可独立配置和切换
- 支持 3 种以上 Embedding 模型
- 相似度检索准确率测试通过

---

#### Task 3.2: 模型配置文件管理（models.yaml）

**来源**: Story 1.5
**负责人**: TBD
**优先级**: P1
**预估工作量**: 2 天
**依赖**: Task 3.1

**子任务**:
- [ ] 设计 models.yaml 配置文件结构
- [ ] 实现 YAML 配置解析和验证（使用 pydantic）
- [ ] 添加配置文件 schema 定义
- [ ] 实现配置热更新机制（文件监听）
- [ ] 创建默认配置模板
- [ ] 添加配置错误提示和验证
- [ ] 编写配置文档

**技术要点**:
```yaml
# config/models.yaml
llm_models:
  default: qwen2.5:7b
  parameters:
    temperature: 0.7
    top_p: 0.9
    max_tokens: 4096

embedding_models:
  default: bge-large-zh
  cache_enabled: true
```

**验收标准**:
- models.yaml 配置正确加载
- 配置修改后自动生效
- 配置错误时显示友好提示

---

#### Task 3.3: 模型健康检查系统

**来源**: Story 1.9
**负责人**: TBD
**优先级**: P1
**预估工作量**: 2 天
**依赖**: Task 3.1

**子任务**:
- [ ] 实现对话模型健康检查测试用例（简单问答）
- [ ] 实现 Embedding 模型健康检查（向量化测试）
- [ ] 模型下载后自动触发健康检查
- [ ] 添加健康检查结果存储和展示
- [ ] 开发自动修复/重新下载机制
- [ ] 生成健康检查报告
- [ ] 添加健康检查 API 接口

**技术要点**:
```python
# src/models/health_check.py
async def check_llm_health(model_name: str) -> HealthCheckResult:
    """测试对话模型是否正常工作"""
    test_prompt = "你好，请回复'健康检查通过'"
    response = await llm.generate(test_prompt)
    return HealthCheckResult(passed=True, latency=0.5)
```

**验收标准**:
- 对话模型健康检查通过
- Embedding 模型健康检查通过
- 失败时提供修复建议

---

#### Task 3.4: 引用溯源系统实现

**来源**: Story 3.5
**负责人**: TBD
**优先级**: P0
**预估工作量**: 4 天
**依赖**: Sprint 2 完成

**子任务**:
- [ ] 设计引用数据结构（文档ID、片段、位置）
- [ ] 实现引用提取算法（从生成文本中提取引用）
- [ ] 添加引用链追踪（追溯到原始文档）
- [ ] 实现引用展示 UI 组件
- [ ] 添加引用点击跳转功能
- [ ] 实现引用准确性验证
- [ ] 编写集成测试

**技术要点**:
```python
# 引用数据结构
class Citation:
    doc_id: str
    chunk_id: str
    source: str  # Jira/Confluence/Local
    url: str
    score: float
    excerpt: str
```

**验收标准**:
- 每个答案显示引用来源
- 引用可点击跳转到原文
- 引用准确性 > 90%

---

#### Task 3.5: 本地文档上传功能

**来源**: Story 4.13
**负责人**: TBD
**优先级**: P1
**预估工作量**: 3 天
**依赖**: Task 3.4

**子任务**:
- [ ] 实现文件上传组件（支持拖拽）
- [ ] 支持多种文件格式（PDF、Word、Markdown、TXT）
- [ ] 实现批量上传功能
- [ ] 添加上传进度显示
- [ ] 实现文档元数据自动提取
- [ ] 上传后自动触发索引
- [ ] 添加文件大小和格式校验
- [ ] 实现文档删除功能

**技术要点**:
```python
# 支持的文件格式
SUPPORTED_FORMATS = ['.pdf', '.docx', '.md', '.txt', '.xlsx']
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
```

**验收标准**:
- 支持拖拽上传文件
- 支持 PDF/Word/Markdown/TXT 格式
- 上传后自动索引并可检索

---

### Sprint 验收标准

**功能验收**:
- [ ] Embedding 模型独立管理系统上线
- [ ] models.yaml 配置文件系统正常工作
- [ ] 模型健康检查机制完成
- [ ] 引用溯源功能完整实现
- [ ] 本地文档上传功能可用

**技术验收**:
- [ ] 代码覆盖率 > 80%
- [ ] 所有单元测试和集成测试通过
- [ ] 代码 Review 通过（无 P0/P1 问题）
- [ ] API 文档更新
- [ ] 配置文件文档完善

**Sprint 1-3 阶段完成度**:
- [ ] ✅ 所有 Sprint 1-3 定义的用户故事完成
- [ ] ✅ 完整的 Ollama 模型管理系统（对话模型 + Embedding模型）
- [ ] ✅ 模型健康检查机制
- [ ] ✅ 基础对话界面原型
- [ ] ✅ 完整的开发文档

---

### Sprint 4 (2026-02-03 ~ 2026-02-16)

**计划目标**: 结果过滤、搜索功能、模型切换 UI

**计划用户故事**:
- [ ] Story 3.7: 检索结果过滤 - Epic 3 (5点)
- [ ] Story 4.5: 搜索功能 - Epic 4 (8点)
- [ ] Story 4.6: 模型切换 UI - Epic 4 (5点)
- [ ] Story 4.7: 同步状态显示 - Epic 4 (8点)

**预估故事点数**: 26 点

---

### Sprint 5 (2026-02-17 ~ 2026-03-02)

**计划目标**: 批量处理、引用展示、用户体验优化

**计划用户故事**:
- [ ] Story 3.8: 批量文档处理 - Epic 3 (8点)
- [ ] Story 4.8: 引用展示优化 - Epic 4 (8点)
- [ ] Story 4.9: 用户体验优化 - Epic 4 (13点)

**预估故事点数**: 29 点

---

## Sprint 里程碑 / Milestones

### v0.2.0 - Enhanced Retrieval (目标: 2026-02-16)
- Sprint 2-4
- 混合检索 + 重排序 + 引用溯源
- Web UI 基础增强

### v0.3.0 - MCP & Multi-user (目标: 2026-04-30)
- Sprint 6-9
- MCP 协议支持
- 多用户认证和权限管理

### v1.0.0 - Production Ready (目标: 2026-08-31)
- Sprint 10-15
- 完整企业级功能
- 性能优化和监控

---

## Sprint 回顾模板 / Sprint Retrospective Template

### Sprint X 回顾 (YYYY-MM-DD)

**做得好的 (What went well)**:
-

**需要改进的 (What could be improved)**:
-

**行动计划 (Action items)**:
- [ ]

**团队速率 (Velocity)**:
- 计划故事点数: X 点
- 完成故事点数: Y 点
- 完成率: Z%

---

## 附录：Sprint 管理最佳实践

### Daily Standup 议程
1. 昨天完成了什么？
2. 今天计划做什么？
3. 遇到什么阻碍？

### Sprint Planning 检查清单
- [ ] 所有用户故事都有明确的验收标准
- [ ] 任务分解足够细（< 1天的粒度）
- [ ] 依赖关系已识别
- [ ] 团队容量已确认
- [ ] 技术风险已评估

### Sprint Review 检查清单
- [ ] 演示所有完成的功能
- [ ] 收集 Stakeholder 反馈
- [ ] 更新 Product Backlog
- [ ] 记录未完成的故事

### Definition of Done (DoD)
- [ ] 代码实现完成
- [ ] 单元测试通过（覆盖率 > 80%）
- [ ] 集成测试通过
- [ ] 代码 Review 通过
- [ ] 文档更新完成
- [ ] 部署到测试环境成功
- [ ] 产品负责人验收通过
