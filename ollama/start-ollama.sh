#!/bin/bash
# 启动 Ollama Docker 容器并下载模型

echo "===== 启动 KT-BOT Ollama 服务 ====="

# 检查 Docker 是否运行
if ! docker ps &> /dev/null; then
    echo "❌ Docker daemon 未运行"
    echo "请先启动 Docker Desktop，然后重新运行此脚本"
    exit 1
fi

# 启动 Ollama 容器
echo "🚀 启动 Ollama 容器..."
docker-compose up -d ollama

# 等待 Ollama 服务启动
echo "⏳ 等待 Ollama 服务启动..."
sleep 5

# 测试连接
echo "🔍 测试 Ollama 连接..."
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "✅ Ollama 服务运行正常"
    
    # 下载默认模型
    echo ""
    echo "📥 开始下载模型 qwen2.5:7b（约 4.7GB，需要几分钟）..."
    docker exec ktbot-ollama ollama pull qwen2.5:7b
    
    echo ""
    echo "✅ 完成！Ollama 已就绪，可以开始使用"
    echo "   访问地址: http://localhost:11434"
else
    echo "❌ Ollama 服务连接失败"
    echo "   请检查 Docker 日志: docker-compose logs ollama"
fi
