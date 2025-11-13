import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import BaseMiddleware
from aiogram.types import Message

from config import settings
from handlers import router
from database.base import AsyncSessionLocal


# Выносим middleware ВНЕ функции main
class SessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        async with AsyncSessionLocal() as session:
            data["session"] = session
            return await handler(event, data)


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Регистрируем middleware
    dp.update.middleware(SessionMiddleware())

    # Подключаем роутеры
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())