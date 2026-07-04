from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.finance import Order
from models.marketplace import ExpertServiceOrder


ORDER_PAYMENT_TIMEOUT_MINUTES = 15


def order_payment_deadline(order: Order) -> datetime:
    return order.created_time + timedelta(minutes=ORDER_PAYMENT_TIMEOUT_MINUTES)


def is_order_payment_expired(order: Order, now: datetime | None = None) -> bool:
    now = now or datetime.now()
    return order.status == "PENDING" and now >= order_payment_deadline(order)


async def expire_pending_orders(session: AsyncSession, now: datetime | None = None) -> int:
    now = now or datetime.now()
    cutoff = now - timedelta(minutes=ORDER_PAYMENT_TIMEOUT_MINUTES)
    result = await session.execute(
        select(Order).where(Order.status == "PENDING", Order.created_time <= cutoff).with_for_update()
    )
    orders = result.scalars().all()
    if not orders:
        return 0

    order_ids = [order.id for order in orders]
    services = (
        await session.execute(
            select(ExpertServiceOrder)
            .where(ExpertServiceOrder.finance_order_id.in_(order_ids))
            .with_for_update()
        )
    ).scalars().all()
    service_by_order_id = {service.finance_order_id: service for service in services}

    for order in orders:
        order.status = "CANCELLED"
        order.updated_time = now
        service = service_by_order_id.get(order.id)
        if service and service.status == "PENDING_PAYMENT":
            service.status = "CANCELLED"
            service.updated_time = now

    await session.commit()
    return len(orders)


async def expire_order_if_unpaid(session: AsyncSession, order: Order, now: datetime | None = None) -> bool:
    now = now or datetime.now()
    if not is_order_payment_expired(order, now):
        return False

    service = await session.scalar(
        select(ExpertServiceOrder)
        .where(ExpertServiceOrder.finance_order_id == order.id)
        .with_for_update()
    )
    order.status = "CANCELLED"
    order.updated_time = now
    if service and service.status == "PENDING_PAYMENT":
        service.status = "CANCELLED"
        service.updated_time = now
    await session.commit()
    await session.refresh(order)
    return True
