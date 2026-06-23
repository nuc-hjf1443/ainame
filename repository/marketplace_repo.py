from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.asset import NamingAsset
from models.finance import Order
from models.marketplace import ExpertProfile, ExpertReport, ExpertReview, ExpertServiceOrder, ExpertServicePackage
from repository.membership_repo import MembershipRepository


class MarketplaceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_expert_for_user(self, user_id: int, approved: bool = False):
        conditions = [ExpertProfile.user_id == user_id]
        if approved:
            conditions.append(ExpertProfile.status == "APPROVED")
        return await self.session.scalar(select(ExpertProfile).where(*conditions))

    async def apply_expert(self, user_id: int, values: dict):
        profile = await self.get_expert_for_user(user_id)
        if profile and profile.status in {"PENDING", "APPROVED", "SUSPENDED"}:
            return None
        if profile:
            for key, value in values.items():
                setattr(profile, key, value)
            profile.status = "PENDING"
            profile.review_note = None
        else:
            profile = ExpertProfile(user_id=user_id, **values)
            self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def _rating(self, expert_id: int):
        row = (await self.session.execute(select(func.avg(ExpertReview.rating), func.count(ExpertReview.id)).where(ExpertReview.expert_id == expert_id))).one()
        return float(row[0] or 0), int(row[1] or 0)

    async def expert_payload(self, profile: ExpertProfile):
        average, count = await self._rating(profile.id)
        data = {column.name: getattr(profile, column.name) for column in ExpertProfile.__table__.columns}
        data.update(average_rating=round(average, 2), review_count=count)
        return data

    async def list_experts(self, page: int, page_size: int, expert_type: str | None, admin: bool = False, status: str | None = None):
        conditions = [] if admin else [ExpertProfile.status == "APPROVED"]
        if admin and status:
            conditions.append(ExpertProfile.status == status)
        if expert_type:
            conditions.append(ExpertProfile.expert_type == expert_type)
        total = await self.session.scalar(select(func.count()).select_from(ExpertProfile).where(*conditions)) or 0
        profiles = (await self.session.execute(select(ExpertProfile).where(*conditions).order_by(ExpertProfile.id.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return [await self.expert_payload(item) for item in profiles], total

    async def get_expert(self, expert_id: int, public: bool = True):
        conditions = [ExpertProfile.id == expert_id]
        if public:
            conditions.append(ExpertProfile.status == "APPROVED")
        profile = await self.session.scalar(select(ExpertProfile).where(*conditions))
        return await self.expert_payload(profile) if profile else None

    async def list_packages(self, expert_type: str | None = None, active_only: bool = True):
        conditions = []
        if active_only:
            conditions.append(ExpertServicePackage.status == "ACTIVE")
        if expert_type:
            conditions.append(ExpertServicePackage.expert_type == expert_type)
        result = await self.session.execute(select(ExpertServicePackage).where(*conditions).order_by(ExpertServicePackage.price, ExpertServicePackage.id))
        return result.scalars().all()

    async def create_package(self, values: dict):
        package = ExpertServicePackage(**values)
        self.session.add(package)
        await self.session.commit()
        await self.session.refresh(package)
        return package

    async def update_package(self, package_id: int, values: dict):
        package = await self.session.get(ExpertServicePackage, package_id)
        if not package:
            return None
        for key, value in values.items():
            setattr(package, key, value)
        await self.session.commit()
        await self.session.refresh(package)
        return package

    async def create_order(self, customer_id: int, values: dict):
        expert = await self.session.scalar(select(ExpertProfile).where(ExpertProfile.id == values["expert_id"], ExpertProfile.status == "APPROVED"))
        package = await self.session.scalar(select(ExpertServicePackage).where(ExpertServicePackage.id == values["package_id"], ExpertServicePackage.status == "ACTIVE"))
        asset = await self.session.scalar(select(NamingAsset).where(NamingAsset.id == values["naming_asset_id"], NamingAsset.user_id == customer_id))
        if (
            not expert
            or not package
            or not asset
            or expert.expert_type != package.expert_type
            or expert.user_id == customer_id
        ):
            return None
        discount_rate = await MembershipRepository(self.session).expert_discount(customer_id)
        amount = (package.price * discount_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        finance = Order(user_id=customer_id, package_id=None, amount=amount, status="PENDING")
        self.session.add(finance)
        await self.session.flush()
        service = ExpertServiceOrder(
            finance_order_id=finance.id,
            customer_id=customer_id,
            original_amount=package.price,
            discount_rate=discount_rate,
            amount=amount,
            **values,
        )
        self.session.add(service)
        await self.session.commit()
        await self.session.refresh(service)
        return service

    async def get_order(self, order_id: int):
        return await self.session.get(ExpertServiceOrder, order_id)

    async def _order_payload(self, service: ExpertServiceOrder):
        finance = await self.session.get(Order, service.finance_order_id)
        expert = await self.session.get(ExpertProfile, service.expert_id)
        package = await self.session.get(ExpertServicePackage, service.package_id)
        asset = await self.session.get(NamingAsset, service.naming_asset_id)
        report = await self.session.scalar(select(ExpertReport).where(ExpertReport.service_order_id == service.id))
        return {
            "id": service.id, "finance_order_id": service.finance_order_id, "customer_id": service.customer_id,
            "expert_id": service.expert_id, "expert_name": expert.display_name, "package_id": service.package_id,
            "package_name": package.name, "naming_asset_id": service.naming_asset_id, "asset_name": asset.name,
            "original_amount": service.original_amount, "discount_rate": service.discount_rate,
            "amount": service.amount, "requirements": service.requirements, "payment_status": finance.status,
            "status": service.status, "rejection_reason": service.rejection_reason, "report": report,
            "created_time": service.created_time,
        }

    async def order_payload(self, service: ExpertServiceOrder):
        return await self._order_payload(service)

    async def list_customer_orders(self, user_id: int, page: int, page_size: int):
        return await self._list_orders(ExpertServiceOrder.customer_id == user_id, page=page, page_size=page_size)

    async def list_expert_orders(self, expert_id: int, page: int, page_size: int, status: str | None):
        conditions = [ExpertServiceOrder.expert_id == expert_id]
        if status:
            conditions.append(ExpertServiceOrder.status == status)
        return await self._list_orders(*conditions, page=page, page_size=page_size)

    async def _list_orders(self, *conditions, page: int, page_size: int):
        total = await self.session.scalar(select(func.count()).select_from(ExpertServiceOrder).where(*conditions)) or 0
        services = (await self.session.execute(select(ExpertServiceOrder).where(*conditions).order_by(ExpertServiceOrder.id.desc()).offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return [await self._order_payload(item) for item in services], total

    async def customer_transition(self, service: ExpertServiceOrder, user_id: int, action: str):
        service = await self.session.scalar(
            select(ExpertServiceOrder)
            .where(ExpertServiceOrder.id == service.id, ExpertServiceOrder.customer_id == user_id)
            .with_for_update()
        )
        if not service:
            return False
        finance = await self.session.scalar(
            select(Order).where(Order.id == service.finance_order_id).with_for_update()
        )
        if not finance:
            return False
        if action == "PAY" and service.status == "PENDING_PAYMENT":
            finance.status, finance.paid_time, service.status = "PAID", datetime.now(), "WAITING_ACCEPT"
        elif action == "CANCEL" and service.status in {"PENDING_PAYMENT", "WAITING_ACCEPT"}:
            finance.status = "CANCELLED" if finance.status == "PENDING" else "REFUNDED"
            service.status = "CANCELLED"
        elif action == "COMPLETE" and service.status == "DELIVERED":
            service.status = "COMPLETED"
        else:
            return False
        await self.session.commit()
        return True

    async def expert_transition(self, service: ExpertServiceOrder, expert_id: int, action: str, reason: str | None = None):
        service = await self.session.scalar(
            select(ExpertServiceOrder)
            .where(ExpertServiceOrder.id == service.id, ExpertServiceOrder.expert_id == expert_id)
            .with_for_update()
        )
        if not service:
            return False
        finance = await self.session.scalar(
            select(Order).where(Order.id == service.finance_order_id).with_for_update()
        )
        if not finance:
            return False
        if action == "ACCEPT" and service.status == "WAITING_ACCEPT":
            service.status = "IN_PROGRESS"
        elif action == "REJECT" and service.status == "WAITING_ACCEPT":
            service.status, service.rejection_reason, finance.status = "CANCELLED", reason, "REFUNDED"
        else:
            return False
        await self.session.commit()
        return True

    async def save_report(self, service: ExpertServiceOrder, expert_id: int, values: dict, submit: bool = False):
        if service.expert_id != expert_id or service.status != "IN_PROGRESS":
            return None
        report = await self.session.scalar(select(ExpertReport).where(ExpertReport.service_order_id == service.id))
        if not report:
            report = ExpertReport(service_order_id=service.id)
            self.session.add(report)
        for key, value in values.items():
            setattr(report, key, value)
        if submit:
            report.status, service.status = "SUBMITTED", "DELIVERED"
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def add_review(self, service: ExpertServiceOrder, user_id: int, values: dict):
        if service.customer_id != user_id or service.status != "COMPLETED":
            return None
        if await self.session.scalar(select(ExpertReview.id).where(ExpertReview.service_order_id == service.id)):
            return None
        review = ExpertReview(service_order_id=service.id, expert_id=service.expert_id, customer_id=user_id, **values)
        self.session.add(review)
        await self.session.commit()
        await self.session.refresh(review)
        return review

    async def review_expert(self, expert_id: int, admin_id: int, status: str, note: str | None):
        profile = await self.session.get(ExpertProfile, expert_id)
        if not profile:
            return None
        profile.status, profile.review_note = status, note
        profile.reviewed_by, profile.reviewed_time = admin_id, datetime.now()
        await self.session.commit()
        await self.session.refresh(profile)
        return profile
