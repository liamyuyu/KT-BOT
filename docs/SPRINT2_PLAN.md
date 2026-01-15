# Sprint 2 任务规划

> **Sprint 周期**: 2026-01-17 ~ 2026-01-30 (2周)
> **Sprint 目标**: 完成 Epic 3 的混合检索和重排序功能，增强 Web UI 基础交互
> **总故事点数**: 29 点

---

## 📋 用户故事清单

### Story 3.3: 混合检索（向量 + BM25） - 13点 ⭐

**Epic**: Epic 3 - RAG 检索引擎
**优先级**: P0 (高)
**预估工作量**: 5-6 天
**依赖**: Sprint 1 完成的向量检索基础

#### 业务价值
实现混合检索策略（向量检索 + BM25 全文检索），提升检索准确率和召回率，特别是对关键词精确匹配的场景。

#### 验收标准

**正向功能**:
- [ ] 实现向量检索（基于语义相似度）- 已有基础，需优化
- [ ] 实现全文检索（BM25 算法，支持中文分词）
- [ ] 实现 RRF（Reciprocal Rank Fusion）融合算法
- [ ] 支持动态调整检索权重（向量 vs 全文）
- [ ] 返回相关度分数（归一化到 0-1）
- [ ] 支持结果去重（基于文档 ID）

**性能标准**:
| 文档规模 | 检索延迟 | Top-K | 目标 |
|---------|---------|-------|------|
| 1K 文档 | < 200ms | 20 | P95 |
| 10K 文档 | < 300ms | 20 | P95 |
| 100K 文档 | < 500ms | 20 | P95 |

- [ ] 向量检索单独延迟 < 150ms（10K 文档）
- [ ] 全文检索单独延迟 < 100ms（10K 文档）
- [ ] RRF 融合计算 < 50ms（Top-20 候选）
- [ ] 支持并发查询：10 并发用户，P95 < 600ms

#### 技术任务分解

##### Task 2.1: BM25 全文检索实现 (4点, 2天)

**子任务**:
1. **安装依赖**
   - [ ] 安装 `rank-bm25` 库 (Python BM25 实现)
   - [ ] 安装 `jieba` 中文分词库
   - [ ] 配置分词词典（自定义词库）

2. **实现 BM25Retriever**
   - [ ] 创建 `src/core/rag/retriever/bm25.py`
   - [ ] 实现 BM25Retriever 类
     - `__init__(documents, k1=1.5, b=0.75)` - 初始化
     - `index_documents(documents)` - 索引文档
     - `search(query, top_k)` - 搜索
     - `update_index(new_documents)` - 更新索引
   - [ ] 中文分词预处理
     - 实现 `tokenize_chinese(text)` 函数
     - 停用词过滤
     - 词性标注（可选）
   - [ ] 实现索引持久化（pickle 保存/加载）

3. **数据模型**
   - [ ] 创建 `BM25SearchResult` 模型
   - [ ] 创建 `BM25Config` 配置类
   - [ ] 更新 `RetrievalResult` 支持 BM25 分数

4. **单元测试**
   - [ ] 测试 BM25 索引构建
   - [ ] 测试中文分词准确性
   - [ ] 测试 BM25 搜索结果
   - [ ] 测试索引持久化和加载
   - 目标：10+ 测试用例，覆盖率 > 90%

**交付物**:
- `src/core/rag/retriever/bm25.py` (~250 行)
- `tests/unit/test_rag/test_bm25_retriever.py` (~150 行)
- 配置文件更新

---

##### Task 2.2: RRF 融合算法实现 (3点, 1.5天)

**子任务**:
1. **实现 HybridRetriever**
   - [ ] 创建 `src/core/rag/retriever/hybrid.py`
   - [ ] 实现 HybridRetriever 类
     - `__init__(vector_retriever, bm25_retriever)` - 初始化
     - `search(query, top_k, weights)` - 混合检索
     - `_rrf_fusion(vector_results, bm25_results, k=60)` - RRF 融合
     - `_normalize_scores(results)` - 分数归一化
     - `_deduplicate(results)` - 结果去重

2. **RRF 算法实现**
   - [ ] 实现 Reciprocal Rank Fusion 公式
     ```python
     score = sum(1 / (k + rank_i)) for each retriever
     ```
   - [ ] 支持可配置的 k 参数（默认 60）
   - [ ] 实现权重调整机制（alpha * vector + (1-alpha) * bm25）

3. **数据模型**
   - [ ] 创建 `HybridSearchResult` 模型
   - [ ] 创建 `HybridConfig` 配置类
   - [ ] 添加 `fusion_method` 枚举（RRF, Weighted, Linear）

4. **单元测试**
   - [ ] 测试 RRF 融合算法正确性
   - [ ] 测试权重调整
   - [ ] 测试结果去重
   - [ ] 测试分数归一化
   - 目标：8+ 测试用例，覆盖率 > 90%

**交付物**:
- `src/core/rag/retriever/hybrid.py` (~200 行)
- `tests/unit/test_rag/test_hybrid_retriever.py` (~120 行)

---

##### Task 2.3: 检索性能优化 (3点, 1.5天)

**子任务**:
1. **并发检索实现**
   - [ ] 使用 asyncio 并发执行向量和 BM25 检索
   - [ ] 实现超时控制（防止慢查询）
   - [ ] 添加检索缓存（LRU Cache）

2. **索引优化**
   - [ ] BM25 索引内存优化（使用 mmap）
   - [ ] 向量索引批量查询优化
   - [ ] 实现增量索引更新（避免全量重建）

3. **性能测试**
   - [ ] 创建性能测试脚本 `tests/performance/test_retrieval_perf.py`
   - [ ] 测试不同文档规模下的延迟
   - [ ] 测试并发查询性能
   - [ ] 生成性能报告

4. **监控指标**
   - [ ] 添加检索耗时日志
   - [ ] 添加命中率统计
   - [ ] 添加融合结果分析

**交付物**:
- 性能优化代码（分散在各 retriever 中）
- `tests/performance/test_retrieval_perf.py` (~200 行)
- 性能测试报告

---

##### Task 2.4: API 和 UI 集成 (3点, 1-2天)

**子任务**:
1. **更新 ChatService**
   - [ ] 修改 `src/api/services/chat_service.py`
   - [ ] 切换到 HybridRetriever
   - [ ] 添加检索策略选择（纯向量/纯BM25/混合）
   - [ ] 更新提示词模板（包含混合检索结果）

2. **更新 API 接口**
   - [ ] 更新 `ChatRequest` 模型
     - 添加 `retrieval_method` 字段（vector/bm25/hybrid）
     - 添加 `hybrid_alpha` 权重参数
   - [ ] 更新 `RetrievedContext` 模型
     - 添加 `retrieval_method` 字段
     - 添加融合后的分数

3. **更新 Gradio UI**
   - [ ] 添加检索策略选择器（Radio/Dropdown）
   - [ ] 添加混合检索权重滑块（0.0-1.0）
   - [ ] 更新结果展示（显示检索方法和分数）

4. **集成测试**
   - [ ] 端到端测试混合检索流程
   - [ ] 测试 API 参数传递
   - [ ] 测试 UI 交互

**交付物**:
- 更新后的 API 和 UI 代码
- 集成测试脚本

---

### Story 3.4: Cross-Encoder 重排序 - 8点 ⭐

**Epic**: Epic 3 - RAG 检索引擎
**优先级**: P0 (高)
**预估工作量**: 3-4 天
**依赖**: Task 2.1-2.4 完成

#### 业务价值
使用 Cross-Encoder 模型对检索结果进行重排序，进一步提升结果相关性和准确度，特别是对复杂查询。

#### 验收标准

**正向功能**:
- [ ] 使用 Cross-Encoder 模型进行重排序（推荐：bge-reranker-large）
- [ ] 支持本地和云端 Re-ranker（可配置切换）
- [ ] 显示重排序后的相关度分数（0-1 范围）
- [ ] 支持配置候选文档数量（default: Top-20）和最终保留数量（default: Top-5）
- [ ] 记录重排序性能指标（耗时、提升幅度）

**性能标准**:
| 候选文档数 | 重排序延迟 | GPU 加速 | CPU |
|-----------|-----------|---------|-----|
| 10 个 | < 100ms | ✅ | < 300ms |
| 20 个 | < 200ms | ✅ | < 600ms |
| 50 个 | < 500ms | ✅ | < 1.5s |

- [ ] 批量重排序（batch_size=4）降低延迟 30%

#### 技术任务分解

##### Task 2.5: Reranker 模型集成 (4点, 2天)

**子任务**:
1. **安装模型和依赖**
   - [ ] 通过 Ollama 下载 `bge-reranker-large` 模型
   - [ ] 或安装 `sentence-transformers` 库
   - [ ] 配置 GPU 支持（如果可用）

2. **实现 CrossEncoderReranker**
   - [ ] 创建 `src/core/rag/reranker/cross_encoder.py`
   - [ ] 实现 CrossEncoderReranker 类
     - `__init__(model_name)` - 初始化模型
     - `rerank(query, documents, top_k)` - 重排序
     - `_batch_score(query, documents, batch_size)` - 批量打分
     - `_normalize_scores(scores)` - 分数归一化

3. **模型封装**
   - [ ] 支持 Ollama 和 HuggingFace 两种加载方式
   - [ ] 实现模型缓存（避免重复加载）
   - [ ] 添加超时控制

4. **数据模型**
   - [ ] 创建 `RerankerResult` 模型
   - [ ] 创建 `RerankerConfig` 配置类
   - [ ] 更新 `RetrievalResult` 添加重排序分数

5. **单元测试**
   - [ ] 测试重排序功能
   - [ ] 测试批量处理
   - [ ] 测试分数归一化
   - 目标：6+ 测试用例

**交付物**:
- `src/core/rag/reranker/cross_encoder.py` (~180 行)
- `tests/unit/test_rag/test_reranker.py` (~100 行)

---

##### Task 2.6: 完整检索流程集成 (4点, 2天)

**子任务**:
1. **更新 RAG Pipeline**
   - [ ] 修改检索流程：Hybrid Retrieval → Reranking → Top-K
   - [ ] 实现三阶段检索：
     ```
     1. 混合检索获取 Top-20 候选
     2. Cross-Encoder 重排序
     3. 返回 Top-5 最终结果
     ```
   - [ ] 添加可配置开关（是否启用重排序）

2. **性能优化**
   - [ ] 实现批量重排序（batch_size=4）
   - [ ] 添加重排序缓存
   - [ ] 并发处理候选文档

3. **更新 API 和 UI**
   - [ ] 添加 `enable_reranking` 参数
   - [ ] 添加 `rerank_top_k` 参数（候选文档数）
   - [ ] 添加 `final_top_k` 参数（最终保留数）
   - [ ] UI 添加重排序开关和参数调整

4. **监控和日志**
   - [ ] 记录重排序耗时
   - [ ] 记录排序变化（before/after）
   - [ ] 统计重排序提升幅度

5. **端到端测试**
   - [ ] 创建 `tests/e2e/test_full_rag_pipeline.py`
   - [ ] 测试完整 RAG 流程
   - [ ] 对比开启/关闭重排序的效果
   - [ ] 性能压测

**交付物**:
- 更新的 ChatService 和 API
- E2E 测试脚本
- 性能对比报告

---

### Story 4.2: 文档管理面板 - 8点 ⭐

**Epic**: Epic 4 - Web UI 界面
**优先级**: P1 (中高)
**预估工作量**: 3-4 天
**依赖**: Sprint 1 完成的基础 UI

#### 业务价值
提供文档管理界面，让用户查看、管理、搜索已同步的文档，了解知识库内容和状态。

#### 验收标准

**正向功能**:
- [ ] 显示已同步的文档列表（表格视图）
- [ ] 显示文档元数据：标题、来源、大小、同步时间、索引状态
- [ ] 支持按来源筛选（Jira/Confluence/本地上传）
- [ ] 支持按状态筛选（已索引/索引中/失败）
- [ ] 支持搜索文档（按标题、内容）
- [ ] 支持排序（按时间、大小、标题）
- [ ] 显示文档统计（总数、已索引数、失败数）
- [ ] 支持手动触发单个/批量同步
- [ ] 支持删除文档和重新索引
- [ ] 支持文档预览（弹窗或侧边栏）
- [ ] 支持批量操作（批量删除、批量重新索引）
- [ ] 支持分页（每页 50 条）

**交互体验**:
- [ ] 文档列表加载 < 1s（1000 文档）
- [ ] 搜索响应 < 500ms
- [ ] 筛选和排序即时生效（< 200ms）
- [ ] 批量操作显示进度条
- [ ] 操作成功/失败有明确提示

#### 技术任务分解

##### Task 2.7: 文档管理后端 API (4点, 2天)

**子任务**:
1. **数据模型设计**
   - [ ] 创建 `DocumentMetadata` 模型
     ```python
     - id: str
     - title: str
     - source: str (jira/confluence/local)
     - source_type: str (issue/page/file)
     - size: int (bytes)
     - created_at: datetime
     - updated_at: datetime
     - indexed_at: datetime
     - status: str (indexed/indexing/failed)
     - error_message: str (optional)
     - chunk_count: int
     ```
   - [ ] 创建 `DocumentList` 响应模型
   - [ ] 创建 `DocumentStats` 统计模型

2. **实现 DocumentService**
   - [ ] 创建 `src/api/services/document_service.py`
   - [ ] 实现文档管理服务
     - `list_documents(page, page_size, filters, sort)` - 列表查询
     - `get_document(doc_id)` - 获取单个文档
     - `search_documents(query)` - 搜索文档
     - `delete_document(doc_id)` - 删除文档
     - `reindex_document(doc_id)` - 重新索引
     - `batch_delete(doc_ids)` - 批量删除
     - `batch_reindex(doc_ids)` - 批量重新索引
     - `get_statistics()` - 获取统计信息

3. **实现 API 端点**
   - [ ] 创建 `src/api/routes/documents.py`
   - [ ] 实现 7 个端点：
     - `GET /api/v1/documents` - 文档列表
     - `GET /api/v1/documents/{id}` - 文档详情
     - `GET /api/v1/documents/search` - 搜索文档
     - `DELETE /api/v1/documents/{id}` - 删除文档
     - `POST /api/v1/documents/{id}/reindex` - 重新索引
     - `POST /api/v1/documents/batch-delete` - 批量删除
     - `POST /api/v1/documents/batch-reindex` - 批量重新索引
     - `GET /api/v1/documents/stats` - 统计信息

4. **存储层实现**
   - [ ] 在 ChromaDB 中存储文档元数据
   - [ ] 实现索引状态追踪
   - [ ] 实现查询优化（索引、缓存）

5. **单元测试**
   - [ ] 测试 DocumentService 各方法
   - [ ] 测试 API 端点
   - 目标：15+ 测试用例

**交付物**:
- `src/api/services/document_service.py` (~300 行)
- `src/api/routes/documents.py` (~200 行)
- `src/api/schemas/document.py` (~100 行)
- `tests/unit/test_api/test_document_service.py` (~200 行)

---

##### Task 2.8: 文档管理 UI 界面 (4点, 2天)

**子任务**:
1. **创建文档管理页面**
   - [ ] 创建 `src/ui/pages/document_page.py`
   - [ ] 实现 DocumentPage 类
   - [ ] 使用 Gradio DataFrame 或 HTML 组件展示表格

2. **UI 组件实现**
   - [ ] 文档列表表格（支持排序）
   - [ ] 来源筛选器（Dropdown/Checkbox）
   - [ ] 状态筛选器（Dropdown/Checkbox）
   - [ ] 搜索框（Textbox）
   - [ ] 统计卡片（Markdown 或 HTML）
   - [ ] 分页控件（Button + Number）
   - [ ] 批量操作按钮（删除、重新索引）
   - [ ] 文档预览弹窗（Modal）

3. **事件处理**
   - [ ] 实现文档列表加载
   - [ ] 实现筛选和搜索
   - [ ] 实现排序
   - [ ] 实现分页
   - [ ] 实现删除确认对话框
   - [ ] 实现批量操作进度提示
   - [ ] 实现文档预览

4. **API 客户端更新**
   - [ ] 更新 `src/ui/utils/api_client.py`
   - [ ] 添加文档管理相关方法
     - `list_documents(page, filters, sort)`
     - `search_documents(query)`
     - `delete_document(doc_id)`
     - `reindex_document(doc_id)`
     - `batch_delete(doc_ids)`
     - `batch_reindex(doc_ids)`
     - `get_stats()`

5. **UI 样式优化**
   - [ ] 表格样式美化
   - [ ] 统计卡片设计
   - [ ] 响应式布局
   - [ ] 加载动画和进度条

6. **集成到主界面**
   - [ ] 更新 `src/ui/app.py`
   - [ ] 添加文档管理标签页
   - [ ] 或添加侧边栏导航

**交付物**:
- `src/ui/pages/document_page.py` (~400 行)
- 更新的 API 客户端
- 更新的主界面

---

## 📊 Sprint 2 时间分配

| 任务 | 故事点 | 预估天数 | 开发者 | 优先级 |
|------|--------|----------|--------|--------|
| Task 2.1: BM25 全文检索 | 4 | 2天 | TBD | P0 |
| Task 2.2: RRF 融合算法 | 3 | 1.5天 | TBD | P0 |
| Task 2.3: 检索性能优化 | 3 | 1.5天 | TBD | P1 |
| Task 2.4: API/UI 集成 | 3 | 1-2天 | TBD | P0 |
| Task 2.5: Reranker 模型集成 | 4 | 2天 | TBD | P0 |
| Task 2.6: 完整流程集成 | 4 | 2天 | TBD | P0 |
| Task 2.7: 文档管理后端 | 4 | 2天 | TBD | P1 |
| Task 2.8: 文档管理 UI | 4 | 2天 | TBD | P1 |
| **总计** | **29点** | **~14天** | - | - |

**并行开发建议**:
- Week 1: Task 2.1-2.4 (混合检索) + Task 2.7 (文档管理后端)
- Week 2: Task 2.5-2.6 (重排序) + Task 2.8 (文档管理 UI)

---

## 🎯 Sprint 2 交付物

### 功能交付
1. **混合检索系统**
   - BM25 全文检索实现
   - RRF 融合算法
   - 向量 + 全文混合检索
   - 可配置权重调整

2. **重排序系统**
   - Cross-Encoder 模型集成
   - 批量重排序优化
   - 完整 RAG Pipeline

3. **文档管理界面**
   - 文档列表和搜索
   - 筛选、排序、分页
   - 批量操作功能
   - 文档统计展示

### 代码交付
- 生产代码: ~1,500 行
  - RAG 检索: ~800 行
  - API: ~300 行
  - UI: ~400 行
- 测试代码: ~600 行
- 文档: 性能测试报告、用户指南更新

### 性能指标
- 混合检索延迟 < 300ms (10K 文档)
- 重排序延迟 < 200ms (Top-20)
- 文档列表加载 < 1s (1000 文档)

---

## ✅ Sprint 2 验收标准

### 功能验收
- [ ] 混合检索（向量 + BM25）正常工作
- [ ] RRF 融合算法返回正确结果
- [ ] Cross-Encoder 重排序提升准确率
- [ ] 文档管理界面完整可用
- [ ] 所有 API 端点测试通过

### 性能验收
- [ ] 混合检索满足性能要求（< 300ms）
- [ ] 重排序满足性能要求（< 200ms）
- [ ] 并发查询稳定（10 并发用户）
- [ ] UI 响应流畅（< 1s 加载）

### 测试验收
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试通过
- [ ] 性能测试通过
- [ ] E2E 测试通过

### 文档验收
- [ ] 代码注释完整
- [ ] API 文档更新
- [ ] 用户指南更新
- [ ] 性能测试报告完成

---

## 📚 参考资料

### 混合检索
- [BM25 算法详解](https://en.wikipedia.org/wiki/Okapi_BM25)
- [Reciprocal Rank Fusion 论文](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- Kotaemon 混合检索实现

### Cross-Encoder
- [bge-reranker-large 模型](https://huggingface.co/BAAI/bge-reranker-large)
- [Sentence-Transformers Reranking](https://www.sbert.net/examples/applications/cross-encoder/README.html)

### UI 设计
- Gradio DataFrame 组件文档
- 表格 UI 最佳实践

---

## 🔄 风险和缓解措施

### 风险 1: BM25 中文分词效果不佳
**影响**: 全文检索准确率低
**缓解**:
- 使用 jieba 精确模式
- 添加自定义词典
- 停用词优化

### 风险 2: Reranker 模型性能慢
**影响**: 延迟超标
**缓解**:
- 使用批量推理
- GPU 加速
- 降低候选文档数量
- 考虑轻量级模型

### 风险 3: 文档管理 UI 复杂度高
**影响**: 开发时间超期
**缓解**:
- 使用 Gradio 原生组件简化实现
- 分阶段交付（MVP 先行）
- 暂缓次要功能（如文档预览）

---

**文档创建**: 2026-01-16
**最后更新**: 2026-01-16
**创建者**: Claude Sonnet 4.5
