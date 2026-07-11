from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.asset import NamingAsset
from models.finance import Order
from models.marketplace import (
    ExpertChatAttachment,
    ExpertChatMessage,
    ExpertChatThread,
    ExpertProfile,
    ExpertReport,
    ExpertReview,
    ExpertServiceOrder,
    ExpertServicePackage,
    ExpertWallet,
    ExpertWalletTransaction,
    ExpertWithdrawal,
)
from models.user import User
from services.order_expiry import expire_order_if_unpaid, expire_pending_orders
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

    async def _chat_thread_payload(self, thread: ExpertChatThread) -> dict[str, Any]:
        expert = await self.session.get(ExpertProfile, thread.expert_id)
        customer = await self.session.get(User, thread.customer_id)
        package = await self.session.get(ExpertServicePackage, thread.package_id)
        latest = await self.session.scalar(
            select(ExpertChatMessage)
            .where(ExpertChatMessage.thread_id == thread.id)
            .order_by(ExpertChatMessage.id.desc())
            .limit(1)
        )
        return {
            "id": thread.id,
            "customer_id": thread.customer_id,
            "customer_name": customer.username if customer else "",
            "expert_id": thread.expert_id,
            "expert_user_id": expert.user_id if expert else 0,
            "expert_name": expert.display_name if expert else "",
            "package_id": thread.package_id,
            "package_name": package.name if package else "",
            "service_order_id": thread.service_order_id,
            "status": thread.status,
            "customer_unread_count": thread.customer_unread_count,
            "expert_unread_count": thread.expert_unread_count,
            "last_message_at": thread.last_message_at,
            "latest_message": latest.content if latest else None,
            "created_time": thread.created_time,
        }

    async def get_chat_thread_detail(self, thread_id: int, user_id: int) -> dict[str, Any] | None:
        thread = await self.get_chat_thread_for_user(thread_id, user_id)
        if not thread:
            return None
        payload = await self._chat_thread_payload(thread)
        package = await self.session.get(ExpertServicePackage, thread.package_id)
        expert = await self.session.get(ExpertProfile, thread.expert_id)
        order = await self.session.get(ExpertServiceOrder, thread.service_order_id) if thread.service_order_id else None
        payload.update(
            order=await self.order_payload(order) if order else None,
            package_price=package.price if package else None,
            expert_type=expert.expert_type if expert else None,
        )
        return payload

    async def create_or_get_chat_thread(self, customer_id: int, expert_id: int, package_id: int) -> ExpertChatThread | None:
        expert = await self.session.scalar(select(ExpertProfile).where(ExpertProfile.id == expert_id, ExpertProfile.status == "APPROVED"))
        package = await self.session.scalar(select(ExpertServicePackage).where(ExpertServicePackage.id == package_id, ExpertServicePackage.status == "ACTIVE"))
        if (
            not expert
            or not package
            or expert.user_id == customer_id
            or expert.expert_type != package.expert_type
            or (expert.expert_level or "STANDARD") != (package.expert_level or "STANDARD")
        ):
            return None
        thread = await self.session.scalar(
            select(ExpertChatThread)
            .where(
                ExpertChatThread.customer_id == customer_id,
                ExpertChatThread.expert_id == expert_id,
                ExpertChatThread.package_id == package_id,
                ExpertChatThread.service_order_id.is_(None),
                ExpertChatThread.status == "OPEN",
            )
            .order_by(ExpertChatThread.id.desc())
            .limit(1)
        )
        if thread:
            return thread
        thread = ExpertChatThread(customer_id=customer_id, expert_id=expert_id, package_id=package_id, status="OPEN")
        self.session.add(thread)
        await self.session.commit()
        await self.session.refresh(thread)
        return thread

    async def list_customer_chat_threads(self, customer_id: int, page: int, page_size: int):
        return await self._list_chat_threads(ExpertChatThread.customer_id == customer_id, page=page, page_size=page_size)

    async def list_expert_chat_threads(self, expert_id: int, page: int, page_size: int):
        return await self._list_chat_threads(ExpertChatThread.expert_id == expert_id, page=page, page_size=page_size)

    async def _list_chat_threads(self, *conditions, page: int, page_size: int):
        total = await self.session.scalar(select(func.count()).select_from(ExpertChatThread).where(*conditions)) or 0
        result = await self.session.execute(
            select(ExpertChatThread)
            .where(*conditions)
            .order_by(
                ExpertChatThread.last_message_at.is_(None),
                ExpertChatThread.last_message_at.desc(),
                ExpertChatThread.id.desc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [await self._chat_thread_payload(thread) for thread in result.scalars().all()], total

    async def get_chat_thread_for_user(self, thread_id: int, user_id: int) -> ExpertChatThread | None:
        thread = await self.session.get(ExpertChatThread, thread_id)
        if not thread:
            return None
        expert = await self.session.get(ExpertProfile, thread.expert_id)
        if thread.customer_id == user_id or (expert and expert.user_id == user_id):
            return thread
        return None

    async def list_chat_messages(self, thread_id: int, user_id: int, page: int, page_size: int):
        thread = await self.get_chat_thread_for_user(thread_id, user_id)
        if not thread:
            return None
        total = await self.session.scalar(select(func.count()).select_from(ExpertChatMessage).where(ExpertChatMessage.thread_id == thread_id)) or 0
        result = await self.session.execute(
            select(ExpertChatMessage)
            .where(ExpertChatMessage.thread_id == thread_id)
            .order_by(ExpertChatMessage.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(reversed(result.scalars().all())), total

    async def _attachments_for_messages(self, message_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
        if not message_ids:
            return {}
        result = await self.session.execute(
            select(ExpertChatAttachment)
            .where(ExpertChatAttachment.message_id.in_(message_ids))
            .order_by(ExpertChatAttachment.id)
        )
        grouped: dict[int, list[dict[str, Any]]] = {}
        for attachment in result.scalars().all():
            grouped.setdefault(attachment.message_id or 0, []).append({
                "id": attachment.id,
                "thread_id": attachment.thread_id,
                "message_id": attachment.message_id,
                "uploader_user_id": attachment.uploader_user_id,
                "file_name": attachment.file_name,
                "file_url": attachment.file_url,
                "file_type": attachment.file_type,
                "file_size": attachment.file_size,
                "created_time": attachment.created_time,
            })
        return grouped

    async def list_chat_messages_payload(self, thread_id: int, user_id: int, page: int, page_size: int):
        result = await self.list_chat_messages(thread_id, user_id, page, page_size)
        if not result:
            return None
        messages, total = result
        attachments = await self._attachments_for_messages([message.id for message in messages])
        return [
            {
                "id": message.id,
                "thread_id": message.thread_id,
                "sender_user_id": message.sender_user_id,
                "content": message.content,
                "read_time": message.read_time,
                "created_time": message.created_time,
                "attachments": attachments.get(message.id, []),
            }
            for message in messages
        ], total

    async def send_chat_message(self, thread_id: int, user_id: int, content: str) -> ExpertChatMessage | None:
        thread = await self.get_chat_thread_for_user(thread_id, user_id)
        if not thread or thread.status != "OPEN":
            return None
        expert = await self.session.get(ExpertProfile, thread.expert_id)
        now = datetime.now()
        message = ExpertChatMessage(thread_id=thread.id, sender_user_id=user_id, content=content.strip(), created_time=now)
        self.session.add(message)
        if thread.customer_id == user_id:
            thread.expert_unread_count += 1
        elif expert and expert.user_id == user_id:
            thread.customer_unread_count += 1
        else:
            return None
        thread.last_message_at = now
        await self.session.commit()
        await self.session.refresh(message)
        return message

    async def add_chat_attachment(self, thread_id: int, user_id: int, values: dict[str, Any]) -> ExpertChatAttachment | None:
        thread = await self.get_chat_thread_for_user(thread_id, user_id)
        if not thread or thread.status != "OPEN":
            return None
        expert = await self.session.get(ExpertProfile, thread.expert_id)
        now = datetime.now()
        file_name = values["file_name"]
        message = ExpertChatMessage(
            thread_id=thread.id,
            sender_user_id=user_id,
            content=f"上传资料：{file_name}",
            created_time=now,
        )
        self.session.add(message)
        await self.session.flush()
        attachment = ExpertChatAttachment(
            thread_id=thread.id,
            message_id=message.id,
            uploader_user_id=user_id,
            file_name=file_name,
            file_url=values["file_url"],
            file_path=values["file_path"],
            file_type=values.get("file_type"),
            file_size=values.get("file_size") or 0,
            created_time=now,
        )
        self.session.add(attachment)
        if thread.customer_id == user_id:
            thread.expert_unread_count += 1
        elif expert and expert.user_id == user_id:
            thread.customer_unread_count += 1
        else:
            return None
        thread.last_message_at = now
        await self.session.commit()
        await self.session.refresh(attachment)
        return attachment

    async def mark_chat_thread_read(self, thread_id: int, user_id: int) -> ExpertChatThread | None:
        thread = await self.get_chat_thread_for_user(thread_id, user_id)
        if not thread:
            return None
        expert = await self.session.get(ExpertProfile, thread.expert_id)
        if thread.customer_id == user_id:
            thread.customer_unread_count = 0
        elif expert and expert.user_id == user_id:
            thread.expert_unread_count = 0
        else:
            return None
        await self.session.execute(
            ExpertChatMessage.__table__.update()
            .where(ExpertChatMessage.thread_id == thread.id, ExpertChatMessage.sender_user_id != user_id, ExpertChatMessage.read_time.is_(None))
            .values(read_time=datetime.now())
        )
        await self.session.commit()
        await self.session.refresh(thread)
        return thread

    async def list_packages(
            self,
            expert_type: str | None = None,
            active_only: bool = True,
            expert_level: str | None = None,
    ):
        conditions = []
        if active_only:
            conditions.append(ExpertServicePackage.status == "ACTIVE")
        if expert_type:
            conditions.append(ExpertServicePackage.expert_type == expert_type)
        if expert_level:
            conditions.append(ExpertServicePackage.expert_level == expert_level)
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

    async def delete_package(self, package_id: int):
        package = await self.session.get(ExpertServicePackage, package_id)
        if not package:
            return None
        in_use = await self.session.scalar(
            select(func.count()).select_from(ExpertServiceOrder).where(ExpertServiceOrder.package_id == package_id)
        ) or 0
        if in_use:
            return False
        await self.session.delete(package)
        await self.session.commit()
        return True

    async def create_order(self, customer_id: int, values: dict):
        chat_thread_id = values.pop("chat_thread_id", None)
        expert = await self.session.scalar(select(ExpertProfile).where(ExpertProfile.id == values["expert_id"], ExpertProfile.status == "APPROVED"))
        package = await self.session.scalar(select(ExpertServicePackage).where(ExpertServicePackage.id == values["package_id"], ExpertServicePackage.status == "ACTIVE"))
        asset = await self.session.scalar(select(NamingAsset).where(NamingAsset.id == values["naming_asset_id"], NamingAsset.user_id == customer_id))
        chat_thread = None
        if chat_thread_id:
            chat_thread = await self.session.scalar(
                select(ExpertChatThread).where(
                    ExpertChatThread.id == chat_thread_id,
                    ExpertChatThread.customer_id == customer_id,
                    ExpertChatThread.expert_id == values["expert_id"],
                    ExpertChatThread.package_id == values["package_id"],
                    ExpertChatThread.status == "OPEN",
                )
            )
            if not chat_thread or chat_thread.service_order_id is not None:
                return None
        if (
            not expert
            or not package
            or not asset
            or expert.expert_type != package.expert_type
            or (expert.expert_level or "STANDARD") != (package.expert_level or "STANDARD")
            or expert.user_id == customer_id
        ):
            return None
        discount_rate = await MembershipRepository(self.session).expert_discount(customer_id)
        amount = (package.price * discount_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        finance = Order(
            user_id=customer_id,
            package_id=None,
            amount=amount,
            status="PENDING",
            order_type="EXPERT_SERVICE",
            payment_provider="MOCK",
            payment_subject=f"{expert.display_name}-{package.name}",
        )
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
        await self.session.flush()
        if chat_thread:
            chat_thread.service_order_id = service.id
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
        reviewed = bool(await self.session.scalar(select(ExpertReview.id).where(ExpertReview.service_order_id == service.id)))
        chat_thread = await self.session.scalar(select(ExpertChatThread).where(ExpertChatThread.service_order_id == service.id))
        return {
            "id": service.id, "finance_order_id": service.finance_order_id, "customer_id": service.customer_id,
            "expert_id": service.expert_id, "expert_name": expert.display_name, "package_id": service.package_id,
            "package_name": package.name, "naming_asset_id": service.naming_asset_id, "asset_name": asset.name,
            "original_amount": service.original_amount, "discount_rate": service.discount_rate,
            "amount": service.amount, "requirements": service.requirements, "payment_status": finance.status,
            "chat_thread_id": chat_thread.id if chat_thread else None,
            "out_trade_no": finance.out_trade_no,
            "status": service.status, "rejection_reason": service.rejection_reason, "report": report,
            "reviewed": reviewed, "created_time": service.created_time,
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
        await expire_pending_orders(self.session)
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
        if await expire_order_if_unpaid(self.session, finance):
            return action == "CANCEL"
        if action == "PAY" and service.status == "PENDING_PAYMENT":
            finance.order_type = finance.order_type or "EXPERT_SERVICE"
            finance.payment_provider = "MOCK"
            finance.status, finance.paid_time, service.status = "PAID", datetime.now(), "WAITING_ACCEPT"
        elif action == "CANCEL" and service.status in {"PENDING_PAYMENT", "WAITING_ACCEPT"}:
            if service.status == "WAITING_ACCEPT" and finance.payment_provider == "ALIPAY_SANDBOX":
                return False
            finance.status = "CANCELLED" if finance.status == "PENDING" else "REFUNDED"
            if finance.status == "REFUNDED":
                finance.refunded_time = datetime.now()
            service.status = "CANCELLED"
        elif action == "COMPLETE" and service.status == "DELIVERED":
            service.status = "COMPLETED"
            await self._settle_completed_order(service)
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
            if finance.payment_provider == "ALIPAY_SANDBOX":
                return False
            service.status, service.rejection_reason, finance.status = "CANCELLED", reason, "REFUNDED"
            finance.refunded_time = datetime.now()
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

    async def _wallet_for_expert(self, expert_id: int, *, lock: bool = False) -> ExpertWallet:
        stmt = select(ExpertWallet).where(ExpertWallet.expert_id == expert_id)
        if lock:
            stmt = stmt.with_for_update()
        wallet = await self.session.scalar(stmt)
        if wallet:
            return wallet
        wallet = ExpertWallet(expert_id=expert_id)
        self.session.add(wallet)
        await self.session.flush()
        return wallet

    def _wallet_payload(self, wallet: ExpertWallet) -> dict[str, Any]:
        return {
            "id": wallet.id,
            "expert_id": wallet.expert_id,
            "available_balance": wallet.available_balance,
            "withdrawing_balance": wallet.withdrawing_balance,
            "total_income": wallet.total_income,
            "total_withdrawn": wallet.total_withdrawn,
            "updated_time": wallet.updated_time or wallet.created_time,
        }

    async def get_wallet(self, expert_id: int) -> dict[str, Any]:
        wallet = await self._wallet_for_expert(expert_id)
        await self.session.commit()
        await self.session.refresh(wallet)
        return self._wallet_payload(wallet)

    async def _settle_completed_order(self, service: ExpertServiceOrder) -> None:
        existing = await self.session.scalar(
            select(ExpertWalletTransaction.id).where(
                ExpertWalletTransaction.transaction_type == "ORDER_SETTLEMENT",
                ExpertWalletTransaction.service_order_id == service.id,
            )
        )
        if existing:
            return
        wallet = await self._wallet_for_expert(service.expert_id, lock=True)
        amount = Decimal(service.amount).quantize(Decimal("0.01"))
        wallet.available_balance += amount
        wallet.total_income += amount
        self.session.add(ExpertWalletTransaction(
            wallet_id=wallet.id,
            expert_id=service.expert_id,
            service_order_id=service.id,
            transaction_type="ORDER_SETTLEMENT",
            amount=amount,
            balance_after=wallet.available_balance,
            note=f"订单 #{service.id} 完成结算",
        ))

    async def list_wallet_transactions(self, expert_id: int, page: int, page_size: int):
        total = await self.session.scalar(
            select(func.count()).select_from(ExpertWalletTransaction).where(ExpertWalletTransaction.expert_id == expert_id)
        ) or 0
        result = await self.session.execute(
            select(ExpertWalletTransaction)
            .where(ExpertWalletTransaction.expert_id == expert_id)
            .order_by(ExpertWalletTransaction.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total

    async def create_withdrawal(self, expert_id: int, values: dict) -> ExpertWithdrawal | None:
        amount = Decimal(values["amount"]).quantize(Decimal("0.01"))
        if amount < Decimal("1.00"):
            return None
        wallet = await self._wallet_for_expert(expert_id, lock=True)
        if wallet.available_balance < amount:
            return None
        wallet.available_balance -= amount
        wallet.withdrawing_balance += amount
        withdrawal = ExpertWithdrawal(
            wallet_id=wallet.id,
            expert_id=expert_id,
            amount=amount,
            alipay_account=values["alipay_account"],
            real_name=values["real_name"],
            status="PENDING",
        )
        self.session.add(withdrawal)
        await self.session.flush()
        self.session.add(ExpertWalletTransaction(
            wallet_id=wallet.id,
            expert_id=expert_id,
            withdrawal_id=withdrawal.id,
            transaction_type="WITHDRAW_REQUEST",
            amount=-amount,
            balance_after=wallet.available_balance,
            note="提现申请冻结余额",
        ))
        await self.session.commit()
        await self.session.refresh(withdrawal)
        return withdrawal

    async def list_withdrawals(self, expert_id: int | None, page: int, page_size: int, status: str | None = None):
        conditions = []
        if expert_id is not None:
            conditions.append(ExpertWithdrawal.expert_id == expert_id)
        if status:
            conditions.append(ExpertWithdrawal.status == status)
        total = await self.session.scalar(select(func.count()).select_from(ExpertWithdrawal).where(*conditions)) or 0
        result = await self.session.execute(
            select(ExpertWithdrawal)
            .where(*conditions)
            .order_by(ExpertWithdrawal.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total

    async def review_withdrawal(self, withdrawal_id: int, admin_id: int, status: str, review_note: str | None):
        withdrawal = await self.session.scalar(
            select(ExpertWithdrawal).where(ExpertWithdrawal.id == withdrawal_id).with_for_update()
        )
        if not withdrawal:
            return None
        if withdrawal.status != "PENDING":
            return withdrawal
        wallet = await self.session.scalar(
            select(ExpertWallet).where(ExpertWallet.id == withdrawal.wallet_id).with_for_update()
        )
        if not wallet or wallet.withdrawing_balance < withdrawal.amount:
            return None
        amount = Decimal(withdrawal.amount).quantize(Decimal("0.01"))
        withdrawal.status = status
        withdrawal.review_note = review_note
        withdrawal.reviewed_by = admin_id
        withdrawal.reviewed_time = datetime.now()
        if status == "APPROVED":
            wallet.withdrawing_balance -= amount
            wallet.total_withdrawn += amount
            tx_amount = Decimal("0.00")
            note = "提现审核通过，等待或已完成人工打款"
        else:
            wallet.withdrawing_balance -= amount
            wallet.available_balance += amount
            tx_amount = amount
            note = "提现审核拒绝，余额退回"
        self.session.add(ExpertWalletTransaction(
            wallet_id=wallet.id,
            expert_id=withdrawal.expert_id,
            withdrawal_id=withdrawal.id,
            transaction_type=f"WITHDRAW_{status}",
            amount=tx_amount,
            balance_after=wallet.available_balance,
            note=note if not review_note else f"{note}：{review_note}",
        ))
        await self.session.commit()
        await self.session.refresh(withdrawal)
        return withdrawal

    async def review_expert(
            self,
            expert_id: int,
            admin_id: int,
            status: str,
            note: str | None,
            expert_level: str | None = None,
    ):
        profile = await self.session.get(ExpertProfile, expert_id)
        if not profile:
            return None
        profile.status, profile.review_note = status, note
        if expert_level:
            profile.expert_level = expert_level
        profile.reviewed_by, profile.reviewed_time = admin_id, datetime.now()
        await self.session.commit()
        await self.session.refresh(profile)
        return profile
