from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.vpn_config import VpnConfig, VpnConfigStatus


async def get_active_vpn(session: AsyncSession, user_id: int, country_code: str) -> VpnConfig | None:
    result = await session.execute(
        select(VpnConfig).where(
            and_(
                VpnConfig.user_id == user_id,
                VpnConfig.country_code == country_code,
                VpnConfig.status == VpnConfigStatus.active,
            )
        )
    )
    return result.scalar_one_or_none()


async def get_active_vpns_for_user(session: AsyncSession, user_id: int) -> list[VpnConfig]:
    result = await session.execute(
        select(VpnConfig).where(
            and_(
                VpnConfig.user_id == user_id,
                VpnConfig.status == VpnConfigStatus.active,
            )
        ).order_by(VpnConfig.expires_at)
    )
    return list(result.scalars().all())


async def create_vpn(
    session: AsyncSession,
    user_id: int,
    country_code: str,
    telegram_user_id: int,
    duration_days: int,
) -> VpnConfig:
    now = datetime.now(timezone.utc)
    config_value = f"VPN-CONFIG-STUB::{country_code}::{telegram_user_id}"
    vpn = VpnConfig(
        user_id=user_id,
        country_code=country_code,
        config_value=config_value,
        status=VpnConfigStatus.active,
        purchased_at=now,
        expires_at=now + timedelta(days=duration_days),
    )
    session.add(vpn)
    await session.flush()
    return vpn


async def extend_vpn(session: AsyncSession, vpn: VpnConfig, duration_days: int) -> VpnConfig:
    """Extend existing active VPN by adding duration_days to its current expires_at."""
    vpn.expires_at = vpn.expires_at + timedelta(days=duration_days)
    return vpn


async def get_expiring_vpns(session: AsyncSession, days_left: int) -> list[VpnConfig]:
    """Return active VPNs that expire in exactly `days_left` days (within 24h window)."""
    now = datetime.now(timezone.utc)
    window_start = now + timedelta(days=days_left - 1)
    window_end = now + timedelta(days=days_left)
    result = await session.execute(
        select(VpnConfig).where(
            and_(
                VpnConfig.status == VpnConfigStatus.active,
                VpnConfig.expires_at > window_start,
                VpnConfig.expires_at <= window_end,
            )
        )
    )
    return list(result.scalars().all())


async def get_expired_vpns(session: AsyncSession) -> list[VpnConfig]:
    """Return active VPNs whose expiry date has passed."""
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(VpnConfig).where(
            and_(
                VpnConfig.status == VpnConfigStatus.active,
                VpnConfig.expires_at <= now,
            )
        )
    )
    return list(result.scalars().all())


async def mark_expired(session: AsyncSession, vpn: VpnConfig) -> None:
    vpn.status = VpnConfigStatus.expired
