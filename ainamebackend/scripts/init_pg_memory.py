import asyncio
import sys
from pathlib import Path

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import settings

DB_URI = settings.POSTGRES_MEMORY_URI


async def setup_memory_db():
    print("正在连接 PostgreSQL...")
    async with AsyncPostgresSaver.from_conn_string(DB_URI) as saver:
        await saver.setup()
    print("✅ PostgreSQL 记忆持久化数据表创建成功！")


if __name__ == "__main__":
    # ⚠️ 专治 Windows 下的异步兼容性报错
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(setup_memory_db())
