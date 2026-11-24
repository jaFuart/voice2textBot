import asyncio, logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ErrorEvent
from app.config import settings
from app.handlers import start_router, voice_router, payments_router
from app.db import init_db
from app.handlers.payments import subscription_reminder_task

logging.basicConfig(level=logging.INFO)

async def on_error(event: ErrorEvent, dispatcher: Dispatcher):
    try:
        if hasattr(event.update, 'message') and event.update.message:
            await event.update.message.answer('Произошла ошибка. Попробуйте позже.')
    except Exception:
        pass

async def main():
    if not settings.tg_token:
        raise SystemExit("Set TG_TOKEN in .env before starting the bot.")
    await init_db()
    bot = Bot(token=settings.tg_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(voice_router)
    dp.include_router(payments_router)
    # Глобальный обработчик ошибок
    dp.errors.register(on_error)
    # Запуск фоновой задачи для напоминаний о подписке
    asyncio.create_task(subscription_reminder_task(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
