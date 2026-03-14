from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.user import User


async def get_or_create_user(session: AsyncSession, telegram_user_id: int, username: str | None) -> User:
    result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
    user = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if user is None:
        user = User(
            telegram_user_id=telegram_user_id,
            username=username,
            accepted_terms=False,
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(user)
        await session.flush()
    else:
        user.last_seen_at = now
        if username:
            user.username = username
    return user


async def get_user(session: AsyncSession, telegram_user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
    return result.scalar_one_or_none()


async def accept_terms(session: AsyncSession, user: User) -> None:
    user.accepted_terms = True
