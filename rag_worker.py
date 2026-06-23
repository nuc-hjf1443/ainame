import asyncio
import json
import sys
import aio_pika
import settings
from core.rag_service import process_and_stor_file


async def process_message(message: aio_pika.IncomingMessage):
    """处理接收到的单条排队任务"""
    try:
        # 失败任务拒绝且不无限重入队；成功退出上下文时才 ACK。
        async with message.process(requeue=False):
            task_data = json.loads(message.body.decode("utf-8"))
            user_id = task_data["user_id"]
            file_path = task_data["file_path"]
            print(f"📦 [Worker 接单] 开始解析用户 {user_id} 的文件: {file_path}")
            # PDF 解析、Ollama 调用和 Chroma 写入都是同步阻塞操作。
            await asyncio.to_thread(process_and_stor_file, file_path, user_id)
            print(f"✅ [Worker 完成] 用户 {user_id} 专属知识库构建完毕！")
    except Exception as exc:
        print(f"❌ [Worker 失败] 错误详情: {exc}")


async def main():
    """启动消费者持续监听"""
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        # 核心限流配置：每次最多只从队列拿 1 个任务，防止内存打满
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(settings.RAG_QUEUE_NAME, durable=True)
        print(f"[*] 🚀 知识库解析 Worker 已启动，正在监听 '{settings.RAG_QUEUE_NAME}' 队列。退出请按CTRL + C")
        await queue.consume(process_message)
        await asyncio.Future()


if __name__ == "__main__":
    # 兼容 Windows 系统的底层异步事件循环机制
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
