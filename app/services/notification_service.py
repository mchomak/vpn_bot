import logging
from datetime import datetime, timezone
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories import vpn_repo
from app.db.models.vpn_config import VpnConfig

logger = logging.getLogger(__name__)


async def _get_user_telegram_id(vpn: VpnConfig) -> int:
    """Resolve telegram_user_id from the loaded relationship."""
    return vpn.user.telegram_user_id


async def notify_expiring(bot: Bot, session: AsyncSession, days_left: int) -> None:
    """Send expiry warning notifications for VPNs expiring in `days_left` days."""
    vpns = await vpn_repo.get_expiring_vpns(session, days_left)
    for vpn in vpns:
        try:
            # Access eager-loaded user relationship
            tg_id = vpn.user.telegram_user_id
            expires_str = vpn.expires_at.strftime("%d.%m.%Y")
            await bot.send_message(
                tg_id,
                f"⚠️ Ваш VPN ({vpn.country_code}) истекает через {days_left} дн. ({expires_str}).\n"
                f"Продлите подписку, чтобы не потерять доступ.",
            )
        except Exception:
            # Silently skip if message can't be delivered
            logger.debug("Failed to notify user for vpn_id=%s", vpn.id)


async def expire_outdated_vpns(session: AsyncSession) -> int:
    """Mark all past-due active VPNs as expired. Returns count of expired records."""
    vpns = await vpn_repo.get_expired_vpns(session)
    for vpn in vpns:
        await vpn_repo.mark_expired(session, vpn)
    if vpns:
        await session.commit()
    return len(vpns)
