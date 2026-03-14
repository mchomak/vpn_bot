import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from app.config import settings
from app.bot.middleware import DbSessionMiddleware, UserMiddleware
from app.bot.handlers import get_main_router
from app.bot.scheduler import setup_scheduler
from app.db.base import async_session_factory

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.webhook_secret or None,
        drop_pending_updates=True,
    )
    logger.info("Webhook set to %s", settings.webhook_url)


async def on_shutdown(bot: Bot) -> None:
    await bot.delete_webhook()
    logger.info("Webhook removed")


def create_app() -> web.Application:
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Middlewares: DB session must come before User middleware
    dp.update.middleware(DbSessionMiddleware(async_session_factory))
    dp.update.middleware(UserMiddleware())

    dp.include_router(get_main_router())

    dp.startup.register(lambda: on_startup(bot))
    dp.shutdown.register(lambda: on_shutdown(bot))

    scheduler = setup_scheduler(bot)

    async def _start_scheduler(_app: web.Application) -> None:
        scheduler.start()

    async def _stop_scheduler(_app: web.Application) -> None:
        scheduler.shutdown(wait=False)

    app = web.Application()
    app.on_startup.append(_start_scheduler)
    app.on_cleanup.append(_stop_scheduler)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret or None,
    ).register(app, path=settings.webhook_path)

    setup_application(app, dp, bot=bot)
    return app


if __name__ == "__main__":
    web.run_app(
        create_app(),
        host=settings.webapp_host,
        port=settings.webapp_port,
    )
