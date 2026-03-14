from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User
from app.db.repositories.user_repo import accept_terms
from app.bot.keyboards.main_menu import main_menu_keyboard, terms_keyboard

router = Router()

TERMS_TEXT = (
    "👋 Добро пожаловать!\n\n"
    "Для использования бота необходимо принять пользовательское соглашение.\n"
    "Нажмите кнопку ниже или ознакомьтесь с текстом по ссылке."
)

MAIN_MENU_TEXT = (
    "🏠 Главное меню\n\n"
    "Выберите нужный раздел:"
)


@router.message(CommandStart())
async def cmd_start(message: Message, user: User) -> None:
    if not user.accepted_terms:
        await message.answer(TERMS_TEXT, reply_markup=terms_keyboard())
    else:
        await message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())


@router.callback_query(lambda c: c.data == "accept_terms")
async def on_accept_terms(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    await accept_terms(session, user)
    await session.commit()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "✅ Вы приняли соглашение. Добро пожаловать!\n\n" + MAIN_MENU_TEXT,
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: CallbackQuery) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(MAIN_MENU_TEXT, reply_markup=main_menu_keyboard())
    await callback.answer()
