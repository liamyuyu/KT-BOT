#!/usr/bin/env python3
"""
数据库初始化脚本

用于创建数据库表和初始化数据。

运行方式:
    python scripts/init_db.py
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.storage.database import init_db, close_db


async def main():
    """初始化数据库"""
    print("🚀 开始初始化数据库...")

    try:
        # 创建所有表
        await init_db()
        print("✅ 数据库表创建成功！")

        print("\n📊 已创建的表:")
        print("  - sync_history (同步历史记录)")
        print("  - sync_config (同步配置)")

        print("\n💡 提示:")
        print("  - 使用 Alembic 进行数据库迁移: alembic upgrade head")
        print("  - 回滚迁移: alembic downgrade -1")
        print("  - 创建新迁移: alembic revision --autogenerate -m \"description\"")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await close_db()

    print("\n✨ 数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())
