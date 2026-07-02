from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_502_BAD_GATEWAY

from core.alipay_service import AlipayClient, AlipayError
from core.quota_service import quota_snapshot
from dependencies import get_current_user, get_session, require_mock_payment_enabled
from models.marketplace import ExpertProfile
from models.user import User
from repository.membership_repo import MembershipRepository
from repository.payment_repo import PaymentRepository
from schemas.membership_schemas import (
    MembershipOrderIn, MembershipOrderOut, MembershipPackageOut, MyProfileOut, MyProfileUpdateIn,
)
from schemas.payment_schemas import AlipayPaymentOut


router = APIRouter(tags=["membership"])


@router.get("/membership/packages", response_model=list[MembershipPackageOut])
async def list_membership_packages(session: AsyncSession = Depends(get_session)):
    return await MembershipRepository(session).list_packages()


@router.post("/membership/orders", response_model=MembershipOrderOut)
async def create_membership_order(data: MembershipOrderIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    order = await MembershipRepository(session).create_order(user.id, data.package_id)
    if not order:
        raise HTTPException(404, detail="充值套餐不存在或已下架")
    return order


@router.post("/membership/orders/{order_id}/alipay", response_model=AlipayPaymentOut)
async def create_membership_alipay_payment(
        order_id: int,
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    repository = PaymentRepository(session)
    order = await repository.prepare_membership_alipay_order(order_id, user.id)
    if not order:
        raise HTTPException(409, detail="充值订单不存在或不能发起支付")
    try:
        payment_url = AlipayClient().build_pay_url(order)
    except AlipayError as exc:
        raise HTTPException(status_code=HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return {"order_id": order.id, "out_trade_no": order.out_trade_no or "", "payment_url": payment_url}


@router.put("/membership/orders/{order_id}/pay", response_model=MyProfileOut)
async def pay_membership_order(
        order_id: int,
        _: None = Depends(require_mock_payment_enabled),
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session),
):
    order, membership = await MembershipRepository(session).pay_order(order_id, user.id)
    if not order:
        raise HTTPException(409, detail="充值订单不存在或不能支付")
    return await build_profile(user, session)


async def build_profile(user: User, session: AsyncSession):
    snapshot = await quota_snapshot(session, user.id)
    expert = await session.scalar(select(ExpertProfile).where(ExpertProfile.user_id == user.id))
    membership, package = snapshot["membership"], snapshot["package"]
    account_type = "认证专家" if expert and expert.status == "APPROVED" else ("管理员" if user.role == "ADMIN" else "普通用户")
    return {
        "id": user.id, "username": user.username, "email": user.email, "bio": user.bio,
        "role": user.role, "account_type": account_type, "expert_status": expert.status if expert else None,
        "created_time": user.created_time, "is_vip": snapshot["is_vip"],
        "vip_package_code": package.package_code if package else None,
        "vip_package_name": package.name if package else None,
        "vip_expires_at": membership.end_time if membership else None,
        "naming_balance": snapshot["naming_balance"],
        "naming_quota": {"used": snapshot["naming_used"], "limit": snapshot["naming_limit"], "remaining": max(0, snapshot["naming_limit"] - snapshot["naming_used"])},
        "visual_quota": {"used": snapshot["visual_used"], "limit": snapshot["visual_limit"], "remaining": max(0, snapshot["visual_limit"] - snapshot["visual_used"])},
    }


@router.get("/me/profile", response_model=MyProfileOut)
async def my_profile(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await build_profile(user, session)


@router.put("/me/profile", response_model=MyProfileOut)
async def update_profile(data: MyProfileUpdateIn, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    values = data.model_dump(exclude_unset=True)
    for key, value in values.items():
        setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return await build_profile(user, session)
