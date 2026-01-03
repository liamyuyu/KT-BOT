# 在 macOS 12 上使用 Docker 运行 Ollama

由于 Ollama 原生支持需要 macOS 14+，在 macOS 12 上我们使用 Docker 来运行 Ollama。

## 前提条件

- ✅ Docker Desktop 已安装
- ✅ Docker daemon 正在运行

## 快速启动

### 方法 1: 使用启动脚本（推荐）

```bash
# 确保 Docker Desktop 正在运行
# 然后执行启动脚本
./scripts/start-ollama.sh
```

脚本会自动：
1. 检查 Docker 状态
2. 启动 Ollama 容器
3. 下载 qwen2.5:7b 模型（约 4.7GB）

### 方法 2: 手动启动

```bash
# 1. 启动 Docker Desktop（如果未运行）

# 2. 启动 Ollama 容器
docker-compose up -d ollama

# 3. 等待服务启动（约 5 秒）
sleep 5

# 4. 测试连接
curl http://localhost:11434/api/version

# 5. 下载模型
docker exec ktbot-ollama ollama pull qwen2.5:7b

# 6. 测试模型
docker exec ktbot-ollama ollama run qwen2.5:7b "你好"
```

## 验证安装

```bash
# 检查容器状态
docker-compose ps

# 查看容器日志
docker-compose logs ollama

# 测试 Ollama API
curl http://localhost:11434/api/tags
```

## 下载其他模型

```bash
# 下载 Embedding 模型
docker exec ktbot-ollama ollama pull bge-large-zh

# 下载其他对话模型
docker exec ktbot-ollama ollama pull llama3.1:8b
docker exec ktbot-ollama ollama pull mistral:7b
```

## 常用命令

```bash
# 启动服务
docker-compose up -d ollama

# 停止服务
docker-compose stop ollama

# 重启服务
docker-compose restart ollama

# 查看日志
docker-compose logs -f ollama

# 进入容器
docker exec -it ktbot-ollama bash

# 列出已下载的模型
docker exec ktbot-ollama ollama list

# 删除模型
docker exec ktbot-ollama ollama rm qwen2.5:7b
```

## 故障排查

### 1. Docker daemon 未运行

**错误**: `Cannot connect to the Docker daemon`

**解决方案**: 启动 Docker Desktop 应用

### 2. 端口占用

**错误**: `port is already allocated`

**解决方案**: 
```bash
# 检查占用端口的进程
lsof -i :11434

# 停止占用端口的进程，或修改 docker-compose.yml 中的端口映射
```

### 3. 下载模型失败

**解决方案**: 
```bash
# 重试下载
docker exec ktbot-ollama ollama pull qwen2.5:7b

# 或使用代理（如果网络不稳定）
docker exec -e HTTPS_PROXY=http://your-proxy:port ktbot-ollama ollama pull qwen2.5:7b
```

## 性能说明

- **CPU 模式**: Docker 运行在 CPU 模式，推理速度较慢
- **内存需求**: 
  - qwen2.5:7b 需要约 8GB RAM
  - qwen2.5:14b 需要约 16GB RAM
- **存储空间**: 每个模型约 4-10GB

## 与项目集成

Ollama 运行在 `http://localhost:11434`，与 `.env` 配置中的 `OLLAMA_HOST` 一致。无需修改代码。

```python
# src/config.py 中的默认配置
ollama_host: str = "http://localhost:11434"
```

## 升级到原生 Ollama

如果将来升级到 macOS 14+，可以：

1. 停止 Docker 容器：`docker-compose stop ollama`
2. 安装原生 Ollama：`brew install ollama`
3. 迁移模型数据（如需要）
4. 重新启动项目

