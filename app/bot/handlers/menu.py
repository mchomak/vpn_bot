from aiogram import Router, F
from aiogram.types import Message
from app.config.settings import settings

router = Router()


@router.message(F.text == "🆘 Помощь")
async def help_handler(message: Message) -> None:
    await message.answer(f"Поддержка: @{settings.support_username}")


@router.message(F.text == "⭐ Отзывы")
async def reviews_handler(message: Message) -> None:
    await message.answer(f"Отзывы: {settings.reviews_link}")


@router.message(F.text == "📜 Правила")
async def rules_handler(message: Message) -> None:
    await message.answer(f"Правила: {settings.rules_link}")
