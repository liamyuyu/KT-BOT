# 📊 性能监控面板 - 快速开始指南

## 🚀 快速启动

### 1. 启动服务

```bash
# 终端 1: 启动 FastAPI 后端
cd /Users/macbook/ai-project/KT-BOT
python src/main.py

# 终端 2: 启动 Gradio UI
python -m src.ui.app
```

### 2. 访问监控面板

打开浏览器访问：
- **UI 监控面板**: http://localhost:7861 → 点击 "📊 监控" Tab
- **API 文档**: http://localhost:7860/docs → 查看 "监控" 分组

---

## 🔍 API 端点测试

### 方式 1: 使用测试脚本

```bash
python scripts/test_metrics_api.py
```

### 方式 2: 使用 curl

```bash
# 系统指标
curl http://localhost:7860/api/v1/metrics/system | jq

# 数据库指标
curl http://localhost:7860/api/v1/metrics/database | jq

# API 性能
curl http://localhost:7860/api/v1/metrics/api | jq

# 检索性能
curl http://localhost:7860/api/v1/metrics/retrieval | jq

# 所有指标
curl http://localhost:7860/api/v1/metrics/all | jq
```

### 方式 3: 使用 Python

```python
import httpx
import asyncio

async def test_metrics():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:7860/api/v1/metrics/all")
        data = response.json()

        print(f"CPU: {data['data']['system']['cpu_percent']}%")
        print(f"内存: {data['data']['system']['memory_percent']}%")
        print(f"数据库连接: {data['data']['database']['pool_checked_out']}/{data['data']['database']['pool_size']}")
        print(f"API 总请求数: {data['data']['api']['total_requests']}")
        print(f"平均响应时间: {data['data']['api']['avg_response_time_ms']:.2f}ms")

asyncio.run(test_metrics())
```

---

## 🧪 运行测试

### 单元测试

```bash
# 测试指标收集器
pytest tests/unit/monitoring/test_metrics_collector.py -v

# 测试性能监控中间件
pytest tests/unit/api/middleware/test_timing.py -v

# 测试 API 端点集成
pytest tests/integration/test_metrics_api.py -v

# 运行所有监控相关测试
pytest tests/unit/monitoring/ tests/unit/api/middleware/ tests/integration/test_metrics_api.py -v
```

### 功能验证

```bash
# 验证模块导入
python -c "from src.monitoring.metrics_collector import get_metrics_collector; print('✓ OK')"
python -c "from src.api.middleware.timing import TimingMiddleware; print('✓ OK')"
python -c "from src.ui.pages.metrics_page import create_metrics_page; print('✓ OK')"

# 验证指标采集
python -c "
from src.monitoring.metrics_collector import get_metrics_collector
collector = get_metrics_collector()
system = collector.get_system_metrics()
print(f'✓ System: CPU={system.cpu_percent}%, Memory={system.memory_percent}%')
db = collector.get_database_metrics()
print(f'✓ Database: Pool={db.pool_size}, Checked out={db.pool_checked_out}')
"
```

---

## 📊 监控面板功能

### 4 个关键指标卡片

1. **CPU 使用率** - 当前 CPU 占用百分比
   - 绿色 (< 70%): 正常
   - 黄色 (70-85%): 警告
   - 红色 (> 85%): 危险

2. **内存使用率** - 当前内存占用百分比
   - 显示可用内存 / 总内存

3. **数据库连接** - 连接池使用情况
   - 显示已签出 / 总连接数
   - 显示连接池使用率

4. **API 响应时间** - 平均响应时间
   - 绿色 (< 100ms): 快
   - 黄色 (100-500ms): 中等
   - 红色 (> 500ms): 慢

### API 性能统计面板

显示 6 个关键指标：
- 总请求数
- 请求速率（请求/分钟）
- 平均响应时间
- P50 响应时间
- P95 响应时间
- P99 响应时间

### 数据库连接池面板

显示 5 个指标：
- 连接池大小
- 使用率
- 已签出连接
- 已签入连接
- 溢出连接

### 最慢端点 Top 10

表格显示：
- 端点名称（方法 + 路径）
- 调用次数
- 平均耗时
- 最大耗时

---

## 🔧 配置说明

### 缓存 TTL 调整

编辑 `src/monitoring/metrics_collector.py`:

```python
class MetricsCollector:
    _cache_ttl: int = 5  # 修改为你想要的秒数
```

### 中间件记录数量

编辑 `src/api/main.py`:

```python
app.add_middleware(TimingMiddleware, max_records=1000)  # 修改记录数量
```

### 跳过监控的端点

编辑 `src/api/middleware/timing.py`:

```python
skip_paths = {
    "/health",
    "/metrics",
    "/api/v1/metrics/...",
    # 添加你想跳过的端点
}
```

---

## 🐛 常见问题

### Q1: 监控面板显示"加载失败"

**解决方案**:
1. 确认 FastAPI 服务已启动：`curl http://localhost:7860/health`
2. 检查日志：`tail -f logs/api.log`
3. 验证端点：`curl http://localhost:7860/api/v1/metrics/all`

### Q2: API 性能指标总是 0

**原因**: 中间件未记录任何请求

**解决方案**:
1. 发送一些测试请求生成数据
2. 确认中间件已注册：检查 `src/api/main.py`

### Q3: CPU 采集很慢

**原因**: `psutil.cpu_percent(interval=1)` 需要 1 秒采样

**解决方案**:
- 这是正常的，首次调用需要 1 秒
- 后续调用会使用缓存（< 10ms）
- 缓存 TTL 为 5 秒

### Q4: 数据库连接池溢出为负数

**原因**: SQLAlchemy AsyncAdaptedQueuePool 实现细节

**解决方案**:
- 已在 `metrics_collector.py` 中处理
- 使用 `max(0, pool.overflow())` 确保非负

---

## 📈 性能基准

### 内存占用
- MetricsCollector 缓存: < 1KB
- TimingMiddleware 记录: ~200KB (1000 条)
- 总额外内存: < 300KB

### 响应时间
- `/metrics/system`: ~1000ms (首次), < 10ms (缓存)
- `/metrics/database`: < 10ms
- `/metrics/api`: < 5ms
- `/metrics/all`: < 1100ms (并发获取)

### CPU 开销
- 系统指标采集: 1 秒 / 次（带缓存）
- 中间件记录: < 0.1ms / 请求
- 统计计算: < 5ms（1000 条记录）

---

## 🎯 最佳实践

### 1. 生成负载测试

```bash
# 使用 ab (Apache Bench)
ab -n 1000 -c 10 http://localhost:7860/api/v1/health

# 使用 wrk
wrk -t4 -c100 -d30s http://localhost:7860/api/v1/health
```

### 2. 监控告警阈值建议

| 指标 | 警告 | 危险 |
|------|------|------|
| CPU 使用率 | > 70% | > 85% |
| 内存使用率 | > 70% | > 85% |
| 磁盘使用率 | > 80% | > 90% |
| 数据库连接使用率 | > 70% | > 90% |
| API P95 响应时间 | > 500ms | > 1000ms |

### 3. 定期查看最慢端点

访问监控面板，重点关注：
1. 平均耗时 > 500ms 的端点
2. 调用次数高但响应慢的端点
3. P95/P99 响应时间差异大的端点

---

## 📚 相关文档

- **实施总结**: `STORY-5.5-IMPLEMENTATION-SUMMARY.md`
- **API 文档**: http://localhost:7860/docs#/监控
- **测试脚本**: `scripts/test_metrics_api.py`

---

**快速链接**:
- UI 监控: http://localhost:7861 → "📊 监控"
- API 文档: http://localhost:7860/docs
- 健康检查: http://localhost:7860/health
