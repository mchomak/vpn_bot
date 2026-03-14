import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import async_session_factory
from app.services.notification_service import notify_expiring, expire_outdated_vpns
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from app.db.models.vpn_config import VpnConfig, VpnConfigStatus

logger = logging.getLogger(__name__)


async def _run_subscription_checks(bot: Bot) -> None:
    async with async_session_factory() as session:
        # Eagerly load user for telegram_user_id access
        from sqlalchemy.orm import selectinload as _sel
        from app.db.models.vpn_config import VpnConfig as _VPN

        async def _load_with_user(days: int) -> list[VpnConfig]:
            from app.db.repositories.vpn_repo import get_expiring_vpns
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            window_start = now + timedelta(days=days - 1)
            window_end = now + timedelta(days=days)
            result = await session.execute(
                select(_VPN)
                .options(_sel(_VPN.user))
                .where(
                    _VPN.status == VpnConfigStatus.active,
                    _VPN.expires_at > window_start,
                    _VPN.expires_at <= window_end,
                )
            )
            return list(result.scalars().all())

        # 3-day warning
        vpns_3d = await _load_with_user(3)
        for vpn in vpns_3d:
            try:
                expires_str = vpn.expires_at.strftime("%d.%m.%Y")
                await bot.send_message(
                    vpn.user.telegram_user_id,
                    f"⚠️ Ваш VPN ({vpn.country_code}) истекает через 3 дня ({expires_str}).\n"
                    "Продлите подписку, чтобы не потерять доступ.",
                )
            except Exception:
                logger.debug("Failed to send 3d warning for vpn_id=%s", vpn.id)

        # 1-day warning
        vpns_1d = await _load_with_user(1)
        for vpn in vpns_1d:
            try:
                expires_str = vpn.expires_at.strftime("%d.%m.%Y")
                await bot.send_message(
                    vpn.user.telegram_user_id,
                    f"🔴 Ваш VPN ({vpn.country_code}) истекает завтра ({expires_str})!\n"
                    "Продлите прямо сейчас.",
                )
            except Exception:
                logger.debug("Failed to send 1d warning for vpn_id=%s", vpn.id)

        # Expire outdated VPNs
        expired_count = await expire_outdated_vpns(session)
        if expired_count:
            logger.info("Marked %d VPN configs as expired", expired_count)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        _run_subscription_checks,
        trigger="cron",
        hour=9,
        minute=0,
        kwargs={"bot": bot},
        id="subscription_check",
        replace_existing=True,
    )
    return scheduler
