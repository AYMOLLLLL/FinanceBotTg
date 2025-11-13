import asyncio
import asyncpg
from config import settings


async def check():
    db_url = settings.POSTGRES_URL.replace('+asyncpg', '')
    conn = await asyncpg.connect(db_url)

    tables = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)

    print("📊 Таблицы в базе:")
    for table in tables:
        print(f"• {table['table_name']}")

    await conn.close()


asyncio.run(check())