# tests/conftest.py
import os
import pytest
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# ⚠️ prilagodi import, če imaš app drugje
from app.main import app

from app.db.database import get_db
from app.db.models import Base  # Base.metadata.create_all mora obstajati


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def engine():
    return create_async_engine(TEST_DB_URL, future=True)


@pytest.fixture(scope="session")
def SessionLocal(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="session", autouse=True)
async def create_test_schema(engine):
    # ustvari shemo 1x za test session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(SessionLocal):
    async with SessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
def env_urls(monkeypatch):
    # da tvoji endpointi ne dobijo None iz dotenv/env
    monkeypatch.setenv("ICAL_URL", "http://ical.test")
    monkeypatch.setenv("OPTIMIZER_URL", "http://optimizer.test/optimize")


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
