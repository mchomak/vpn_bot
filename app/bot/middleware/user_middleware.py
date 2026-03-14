from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.repositories.user_repo import get_or_create_user


class UserMiddleware(BaseMiddleware):
    """
    Resolve the current user from DB on every update.
    Injects `user` into handler data.
    Also updates last_seen_at and username automatically.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Extract telegram user from the update
        from_user = None
        if hasattr(event, "message") and event.message:
            from_user = event.message.from_user
        elif hasattr(event, "callback_query") and event.callback_query:
            from_user = event.callback_query.from_user

        if from_user:
            session: AsyncSession = data["session"]
            user = await get_or_create_user(
                session,
                telegram_user_id=from_user.id,
                username=from_user.username,
            )
            await session.commit()
            data["user"] = user
        else:
            data["user"] = None

        return await handler(event, data)
