import asyncio
from database.base import engine, Base
from database.models import User, Expense, Income

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)  # Удаляем всё старое
        await conn.run_sync(Base.metadata.create_all)  # Создаём новое
    print("✅ Таблицы созданы напрямую через SQLAlchemy!")

if __name__ == "__main__":
    asyncio.run(create_tables())