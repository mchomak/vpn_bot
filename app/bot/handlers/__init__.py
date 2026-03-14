from aiogram import Router
from . import start, menu, vpn_buy, my_vpns


def get_main_router() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(menu.router)
    router.include_router(vpn_buy.router)
    router.include_router(my_vpns.router)
    return router
