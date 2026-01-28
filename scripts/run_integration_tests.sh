#!/bin/bash
#
# 集成测试运行脚本
#
# 运行所有的集成测试，包括端到端测试、性能测试和错误处理测试。
#

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$PROJECT_ROOT"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  数据同步系统 - 集成测试套件${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

echo -e "${GREEN}📁 项目目录: ${PROJECT_ROOT}${NC}"
echo -e "${GREEN}🔧 PYTHONPATH: ${PYTHONPATH}${NC}\n"

# 检查 pytest 是否安装
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest 未安装${NC}"
    echo -e "${YELLOW}   安装: pip install pytest pytest-asyncio${NC}"
    exit 1
fi

# 检查数据库是否可用
echo -e "${BLUE}🔍 检查测试环境...${NC}"

# 测试类型
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    all)
        echo -e "${GREEN}📋 运行所有集成测试${NC}\n"
        pytest tests/integration/ -v --tb=short
        ;;

    e2e)
        echo -e "${GREEN}📋 运行端到端测试${NC}\n"
        pytest tests/integration/test_sync_end_to_end.py -v --tb=short
        ;;

    performance)
        echo -e "${GREEN}📋 运行性能测试${NC}\n"
        pytest tests/integration/test_sync_performance.py -v -s --tb=short
        ;;

    error)
        echo -e "${GREEN}📋 运行错误处理测试${NC}\n"
        pytest tests/integration/test_sync_error_handling.py -v --tb=short
        ;;

    quick)
        echo -e "${GREEN}📋 运行快速测试（排除慢速测试）${NC}\n"
        pytest tests/integration/ -v --tb=short -m "not slow"
        ;;

    *)
        echo -e "${RED}❌ 未知的测试类型: $TEST_TYPE${NC}"
        echo -e "${YELLOW}用法: $0 [all|e2e|performance|error|quick]${NC}"
        exit 1
        ;;
esac

# 检查测试结果
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  ✅ 所有测试通过！${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}\n"
else
    echo -e "\n${RED}════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ 部分测试失败${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}\n"
    exit 1
fi
