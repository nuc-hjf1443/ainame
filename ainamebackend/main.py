import asyncio
import logging
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Depends
import settings
from fastapi_mail import FastMail, MessageSchema, MessageType
from routers.auth_router import router as auth_router
from routers.name_router import router as name_router
from routers.rag_router import router as rag_router
from routers.admin_router import router as admin_router
from routers.visual_router import router as visual_router
from routers.asset_router import router as asset_router
from routers.community_router import router as community_router
from routers.marketplace_router import router as marketplace_router
from routers.admin_marketplace_router import router as admin_marketplace_router
from routers.membership_router import router as membership_router
from routers.payment_router import router as payment_router

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from core.workflow import init_workflow_graph, close_workflow_graph
from core.order_expiry import expire_pending_orders
from models import AsyncSessionFactory


logger = logging.getLogger(__name__)


async def expire_pending_orders_loop():
    while True:
        session = AsyncSessionFactory()
        try:
            count = await expire_pending_orders(session)
            if count:
                logger.info("Expired %s stale pending orders", count)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Failed to expire stale pending orders")
        finally:
            await session.close()
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 服务启动时，安全地初始化带记忆的工作流
    await init_workflow_graph()
    order_expiry_task = asyncio.create_task(expire_pending_orders_loop())
    try:
        yield
    finally:
        order_expiry_task.cancel()
        try:
            await order_expiry_task
        except asyncio.CancelledError:
            pass
        # 服务停止时，清理数据库连接
        await close_workflow_graph()


app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(name_router)
app.include_router(rag_router)
app.include_router(admin_router)
app.include_router(visual_router)
app.include_router(asset_router)
app.include_router(community_router)
app.include_router(marketplace_router)
app.include_router(admin_marketplace_router)
app.include_router(membership_router)
app.include_router(payment_router)
app.mount(
    "/uploads/visuals",
    StaticFiles(directory=settings.BASE_DIR / "uploads" / "visuals", check_dir=False),
    name="visuals",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许请求的源列表
    allow_credentials=True,  # 允许携带 Cookie/凭证
    allow_methods=["*"],  # 允许的请求方法（"GET", "POST", "PUT", "DELETE" 等，"*" 表示全部允许）
    allow_headers=["*"],  # 允许的请求头（"*" 表示全部允许）
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


from dependencies import get_email


@app.get("/mail/test")
async def mail_test(email: str, mail: FastMail = Depends(get_email)):
    #  1.准备邮件对象
    message = MessageSchema(
        subject="ainame验证码",
        recipients=[email],
        body=f"Hello {email}",  # 验证码是生产的
        subtype=MessageType.plain)

    await  mail.send_message(message)
    return {"message": "邮件发送成功！"}
