"""
Pytest 配置文件

为集成测试提供共享的 fixtures 和配置。
"""

import pytest


def pytest_configure(config):
    """配置 pytest"""
    # 注册自定义标记
    config.addinivalue_line(
        "markers",
        "slow: 标记运行时间较长的测试"
    )
    config.addinivalue_line(
        "markers",
        "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers",
        "performance: 标记性能测试"
    )


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
