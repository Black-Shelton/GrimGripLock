import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher

import database as db
from config import BOT_TOKEN, ADMIN_IDS, PORT
from menu import register_menu_handlers
from admin import register_admin_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bot")


# ======================================================================
# HEALTH-СЕРВЕР ДЛЯ RENDER + UPTIMEROBOT
# Render Web Service требует открытый порт $PORT. UptimeRobot стучится
# на этот адрес каждые 5 минут, чтобы бесплатный сервис не засыпал.
# ======================================================================
async def _ok(request):
    return web.Response(text="OK")


async def start_health_server():
    app = web.Application()
    app.router.add_get("/", _ok)        # GET и HEAD (aiohttp добавляет HEAD сам)
    app.router.add_get("/health", _ok)
    runner = web.AppRunner(app, access_log=None)  # без спама в логах от пингов
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info("health-сервер слушает 0.0.0.0:%s", PORT)
    return runner


async def idle_forever():
    while True:
        await asyncio.sleep(3600)


async def main():
    # Порт открываем первым делом, иначе Render посчитает деплой упавшим
    await start_health_server()

    if not BOT_TOKEN:
        log.error("BOT_TOKEN не задан (Render -> Environment -> BOT_TOKEN или setting.env)")
        await idle_forever()

    try:
        bot = Bot(token=BOT_TOKEN)
    except Exception as e:
        log.error("Некорректный BOT_TOKEN: %s", e)
        await idle_forever()

    dp = Dispatcher()

    register_menu_handlers(dp)
    register_admin_handlers(dp)

    await db.init_db()

    print("Бот запущен...")
    if ADMIN_IDS:
        print(f"Админы: {ADMIN_IDS}")
    else:
        print("⚠️ ADMIN_IDS не задан")

    try:
        # На случай старого вебхука: иначе polling не получит апдейты
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot)
    except Exception:
        log.exception("Поллинг остановился")
        # Не падаем: порт остаётся открытым, чтобы Render не крутил рестарты по кругу
        await idle_forever()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
