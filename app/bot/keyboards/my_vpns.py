from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.db.models.vpn_config import VpnConfig
from app.config.vpn_catalog import catalog


def my_vpns_keyboard(vpns: list[VpnConfig]) -> InlineKeyboardMarkup:
    rows = []
    for vpn in vpns:
        server = catalog.get_server(vpn.country_code)
        country_title = server.title if server else vpn.country_code
        flag = server.flag if server else ""
        expires_str = vpn.expires_at.strftime("%d.%m.%Y")
        rows.append([
            InlineKeyboardButton(
                text=f"{flag} {country_title} · до {expires_str}",
                callback_data=f"resend_config:{vpn.id}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)
