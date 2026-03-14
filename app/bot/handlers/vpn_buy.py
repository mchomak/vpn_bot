import uuid
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User
from app.config.vpn_catalog import catalog
from app.services.purchase_service import process_payment
from app.bot.keyboards.vpn_buy import (
    personal_vpn_keyboard,
    countries_keyboard,
    plans_keyboard,
    payment_keyboard,
)

router = Router()

PERSONAL_VPN_TEXT = (
    "🔒 <b>Личный VPN</b>\n\n"
    "Высокоскоростной приватный VPN только для вас.\n"
    "Никаких ограничений скорости и трафика.\n\n"
    "Выберите действие:"
)


def _require_terms(user: User) -> bool:
    """Return True if user has not accepted terms (should block action)."""
    return not user.accepted_terms


@router.message(F.text == "🔒 Личный VPN")
async def personal_vpn_menu(message: Message, user: User) -> None:
    if _require_terms(user):
        await message.answer("Сначала примите соглашение — отправьте /start")
        return
    await message.answer(PERSONAL_VPN_TEXT, reply_markup=personal_vpn_keyboard(), parse_mode="HTML")


@router.callback_query(lambda c: c.data == "vpn_buy")
async def show_countries(callback: CallbackQuery, user: User) -> None:
    if _require_terms(user):
        await callback.answer("Сначала примите соглашение", show_alert=True)
        return
    await callback.message.edit_text("🌍 Выберите страну:", reply_markup=countries_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_personal_vpn")
async def back_to_personal_vpn(callback: CallbackQuery) -> None:
    await callback.message.edit_text(PERSONAL_VPN_TEXT, reply_markup=personal_vpn_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_countries")
async def back_to_countries(callback: CallbackQuery) -> None:
    await callback.message.edit_text("🌍 Выберите страну:", reply_markup=countries_keyboard())
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("country:"))
async def show_plans(callback: CallbackQuery, user: User) -> None:
    if _require_terms(user):
        await callback.answer("Сначала примите соглашение", show_alert=True)
        return
    country_code = callback.data.split(":")[1]
    server = catalog.get_server(country_code)
    if not server:
        await callback.answer("Страна недоступна", show_alert=True)
        return
    await callback.message.edit_text(
        f"{server.flag} {server.title} — выберите тариф:",
        reply_markup=plans_keyboard(country_code),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("back_to_plans:"))
async def back_to_plans(callback: CallbackQuery) -> None:
    country_code = callback.data.split(":")[1]
    server = catalog.get_server(country_code)
    title = f"{server.flag} {server.title}" if server else country_code
    await callback.message.edit_text(
        f"{title} — выберите тариф:",
        reply_markup=plans_keyboard(country_code),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("plan:"))
async def show_payment(callback: CallbackQuery, user: User) -> None:
    if _require_terms(user):
        await callback.answer("Сначала примите соглашение", show_alert=True)
        return
    _, country_code, plan_key = callback.data.split(":")
    server = catalog.get_server(country_code)
    if not server:
        await callback.answer("Страна недоступна", show_alert=True)
        return
    plan = server.get_plan(plan_key)
    if not plan:
        await callback.answer("Тариф недоступен", show_alert=True)
        return

    # Generate a checkout_id for idempotency (one per user session click)
    checkout_id = str(uuid.uuid4())

    text = (
        f"💳 <b>Оплата</b>\n\n"
        f"🌍 Страна: {server.flag} {server.title}\n"
        f"📦 Тариф: {plan.title}\n"
        f"⏱ Срок: {plan.duration_days} дней\n"
        f"💰 Сумма: {plan.price} ₽\n\n"
        f"Выберите способ оплаты:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=payment_keyboard(country_code, plan_key, checkout_id),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data and c.data.startswith("pay:"))
async def process_pay(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    if _require_terms(user):
        await callback.answer("Сначала примите соглашение", show_alert=True)
        return

    # pay:<method>:<country>:<plan>:<checkout_id>
    parts = callback.data.split(":")
    if len(parts) != 5:
        await callback.answer("Некорректный запрос", show_alert=True)
        return
    _, method, country_code, plan_key, checkout_id = parts

    server = catalog.get_server(country_code)
    plan = server.get_plan(plan_key) if server else None
    if not server or not plan:
        await callback.answer("Тариф или страна недоступны", show_alert=True)
        return

    # Disable button immediately to prevent double-click UX
    await callback.answer("⏳ Обрабатываем оплату...")

    tx, vpn, is_new = await process_payment(
        session=session,
        user_id=user.id,
        telegram_user_id=callback.from_user.id,
        country_code=country_code,
        plan_key=plan_key,
        plan_title=plan.title,
        duration_days=plan.duration_days,
        amount=plan.price,
        payment_method=method,
        checkout_id=checkout_id,
    )

    expires_str = vpn.expires_at.strftime("%d.%m.%Y")
    action_text = "создан" if is_new else "продлён"

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        f"✅ <b>Оплата прошла успешно!</b>\n\n"
        f"VPN {action_text} для {server.flag} {server.title}\n"
        f"Действует до: <b>{expires_str}</b>\n\n"
        f"Ваш конфиг отправлен ниже 👇",
        parse_mode="HTML",
    )
    await callback.message.answer(
        f"<code>{vpn.config_value}</code>",
        parse_mode="HTML",
    )
