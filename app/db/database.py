import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


DATABASE_URL = "sqlite+aiosqlite:////app/data/datoteka.db"

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session