from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User
from app.db.models.vpn_config import VpnConfig, VpnConfigStatus
from app.db.repositories.vpn_repo import get_active_vpns_for_user
from app.bot.keyboards.my_vpns import my_vpns_keyboard
from app.config.vpn_catalog import catalog

router = Router()


@router.message(F.text == "📋 Мои VPN")
async def my_vpns_handler(message: Message, user: User, session: AsyncSession) -> None:
    if not user.accepted_terms:
        await message.answer("Сначала примите соглашение — отправьте /start")
        return

    vpns = await get_active_vpns_for_user(session, user.id)
    if not vpns:
        await message.answer("У вас нет активных VPN.\nНажмите 🔒 Личный VPN, чтобы купить.")
        return

    await message.answer(
        f"📋 Ваши активные VPN ({len(vpns)}):\n\n"
        "Нажмите на VPN, чтобы получить конфиг ещё раз:",
        reply_markup=my_vpns_keyboard(vpns),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("resend_config:"))
async def resend_config(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    vpn_id = int(callback.data.split(":")[1])

    result = await session.execute(
        select(VpnConfig).where(
            VpnConfig.id == vpn_id,
            VpnConfig.user_id == user.id,
            VpnConfig.status == VpnConfigStatus.active,
        )
    )
    vpn = result.scalar_one_or_none()

    if not vpn:
        await callback.answer("VPN не найден или уже истёк", show_alert=True)
        return

    server = catalog.get_server(vpn.country_code)
    country_title = f"{server.flag} {server.title}" if server else vpn.country_code
    expires_str = vpn.expires_at.strftime("%d.%m.%Y")

    await callback.message.answer(
        f"🔑 Конфиг для {country_title} (до {expires_str}):\n\n"
        f"<code>{vpn.config_value}</code>",
        parse_mode="HTML",
    )
    await callback.answer()
