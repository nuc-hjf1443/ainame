import asyncio
import json
import logging
from pathlib import Path

import aio_pika
import anyio
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status

import settings
from core.auth import AuthHandler

auth_handler = AuthHandler()
router = APIRouter(prefix="/knowledge", tags=["知识库"])
logger = logging.getLogger(__name__)
UPLOAD_DIR = settings.BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# RabbitMQ 连接配置 协议://用户名:密码@主机地址:端口号
RABBITMQ_CONNECT_TIMEOUT_SECONDS = 5


async def send_to_queue(message_dict: dict):
    """异步将任务发送到 RabbitMQ 队列"""
    try:
        # HTTP 请求只负责投递一次，不使用会持续重连的 connect_robust。
        connection = await asyncio.wait_for(
            aio_pika.connect(settings.RABBITMQ_URL),
            timeout=RABBITMQ_CONNECT_TIMEOUT_SECONDS,
        )
        async with connection:
            channel = await connection.channel(publisher_confirms=True)
            queue = await channel.declare_queue(settings.RAG_QUEUE_NAME, durable=True)
            message_body = json.dumps(message_dict).encode("utf-8")
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=message_body,
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                ),
                routing_key=queue.name,
            )
    except Exception as exc:
        logger.exception("RabbitMQ task publishing failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="知识库任务队列暂不可用，请稍后重试",
        ) from exc


@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_file(
        file: UploadFile = File(...),
        user_id: int = Depends(auth_handler.auth_access_dependency),
):
    """
    用户上传专属参考文件（TXT/PDF）
    """
    filename = Path(file.filename or "").name
    if not filename or Path(filename).suffix.lower() not in {".txt", ".pdf"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 TXT 和 PDF 文件",
        )

    file_path = (UPLOAD_DIR / f"{user_id}_{filename}").resolve()
    async with await anyio.open_file(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            await buffer.write(chunk)

    task_message = {
        "user_id": user_id,
        "file_path": str(file_path),
    }
    await send_to_queue(task_message)
    return {
        "result": "success",
        "message": f"文件 {file.filename} 上传成功！后台正在为您构建专属知识库，请稍候测试起名功能。"
    }
