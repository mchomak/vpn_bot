from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.config.vpn_catalog import catalog, VpnServer, Plan


def personal_vpn_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Купить", callback_data="vpn_buy")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main")],
        ]
    )


def countries_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for server in catalog.servers():
        rows.append([
            InlineKeyboardButton(
                text=f"{server.flag} {server.title}",
                callback_data=f"country:{server.code}",
            )
        ])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_personal_vpn")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def plans_keyboard(country_code: str) -> InlineKeyboardMarkup:
    server = catalog.get_server(country_code)
    rows = []
    if server:
        for plan in server.plans:
            rows.append([
                InlineKeyboardButton(
                    text=f"{plan.title} — {plan.price} ₽",
                    callback_data=f"plan:{country_code}:{plan.key}",
                )
            ])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_countries")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_keyboard(country_code: str, plan_key: str, checkout_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="💎 Crypto",
                callback_data=f"pay:crypto:{country_code}:{plan_key}:{checkout_id}",
            )],
            [InlineKeyboardButton(
                text="💳 RUB",
                callback_data=f"pay:rub:{country_code}:{plan_key}:{checkout_id}",
            )],
            [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"back_to_plans:{country_code}",
            )],
        ]
    )
