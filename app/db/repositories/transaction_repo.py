from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.transaction import Transaction, TransactionStatus


async def get_by_idempotency_key(session: AsyncSession, key: str) -> Transaction | None:
    result = await session.execute(select(Transaction).where(Transaction.idempotency_key == key))
    return result.scalar_one_or_none()


async def create_transaction(
    session: AsyncSession,
    user_id: int,
    country_code: str,
    plan_key: str,
    plan_title: str,
    duration_days: int,
    amount: int,
    idempotency_key: str,
) -> Transaction:
    tx = Transaction(
        user_id=user_id,
        country_code=country_code,
        plan_key=plan_key,
        plan_title=plan_title,
        duration_days=duration_days,
        amount=amount,
        idempotency_key=idempotency_key,
        status=TransactionStatus.pending,
    )
    session.add(tx)
    await session.flush()
    return tx


async def mark_paid(session: AsyncSession, tx: Transaction, payment_method: str) -> None:
    tx.status = TransactionStatus.paid
    tx.payment_method = payment_method
    tx.paid_at = datetime.now(timezone.utc)
