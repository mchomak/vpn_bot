import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories import transaction_repo, vpn_repo
from app.db.models.transaction import Transaction
from app.db.models.vpn_config import VpnConfig


def make_idempotency_key(telegram_user_id: int, country_code: str, plan_key: str, ts_bucket: str) -> str:
    """
    Build an idempotency key scoped to user+country+plan+time-bucket.
    ts_bucket is e.g. the ISO date string so the same purchase within
    the same day gets the same key and won't double-charge.
    """
    return f"{telegram_user_id}:{country_code}:{plan_key}:{ts_bucket}"


async def process_payment(
    session: AsyncSession,
    user_id: int,
    telegram_user_id: int,
    country_code: str,
    plan_key: str,
    plan_title: str,
    duration_days: int,
    amount: int,
    payment_method: str,
    checkout_id: str,
) -> tuple[Transaction, VpnConfig, bool]:
    """
    Process a VPN purchase payment.

    Returns (transaction, vpn_config, is_new_vpn).
    is_new_vpn=False means an existing VPN was extended.

    Double-click protection: if a transaction with the same checkout_id
    already exists and is paid, return it without creating a new one.
    """
    # Guard: check idempotency
    existing_tx = await transaction_repo.get_by_idempotency_key(session, checkout_id)
    if existing_tx is not None and existing_tx.status.value == "paid":
        # Already processed — find the associated VPN and return early
        vpn = await vpn_repo.get_active_vpn(session, user_id, country_code)
        return existing_tx, vpn, False  # type: ignore[return-value]

    # Create transaction record
    tx = await transaction_repo.create_transaction(
        session=session,
        user_id=user_id,
        country_code=country_code,
        plan_key=plan_key,
        plan_title=plan_title,
        duration_days=duration_days,
        amount=amount,
        idempotency_key=checkout_id,
    )

    # Mark as paid immediately (stub payment)
    await transaction_repo.mark_paid(session, tx, payment_method)

    # Create or extend VPN
    existing_vpn = await vpn_repo.get_active_vpn(session, user_id, country_code)
    if existing_vpn is not None:
        vpn = await vpn_repo.extend_vpn(session, existing_vpn, duration_days)
        is_new = False
    else:
        vpn = await vpn_repo.create_vpn(
            session=session,
            user_id=user_id,
            country_code=country_code,
            telegram_user_id=telegram_user_id,
            duration_days=duration_days,
        )
        is_new = True

    await session.commit()
    return tx, vpn, is_new
