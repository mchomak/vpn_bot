from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from app.config.settings import settings


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔒 Личный VPN"), KeyboardButton(text="📋 Мои VPN")],
            [KeyboardButton(text="🆘 Помощь"), KeyboardButton(text="⭐ Отзывы")],
            [KeyboardButton(text="📜 Правила")],
        ],
        resize_keyboard=True,
    )


def terms_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data="accept_terms")],
            [InlineKeyboardButton(text="📄 Соглашение", url=settings.terms_link)],
        ]
    )
