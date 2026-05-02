import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

db_url = db_url.replace("sslmode=require", "ssl=require").replace("&channel_binding=require", "")

async def main():
    engine = create_async_engine(db_url, echo=True)
    try:
        async with engine.begin() as conn:
            print("Successfully connected!")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
