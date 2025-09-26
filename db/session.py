from contextlib import asynccontextmanager

from sqlalchemy import text

from db.base import AsyncSessionFactory

@asynccontextmanager
async def get_db_session():
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()