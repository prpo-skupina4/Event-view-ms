# tests/conftest.py
import pytest
import asyncio
import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.api.event_view import get_current_user_id
from app.db.database import get_db
from app.db.models import Base

TEST_DB_URL = "sqlite+pysqlite:///:memory:"


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[get_current_user_id] = lambda: 7
    yield
    app.dependency_overrides.pop(get_current_user_id, None)

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def SessionLocal(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def db_session(SessionLocal) -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def override_get_db(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def env_urls(monkeypatch):
    monkeypatch.setenv("ICAL_URL", "http://ical.test")
    monkeypatch.setenv("OPTIMIZER_URL", "http://optimizer.test/optimize")



@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def close_event_loop():
    yield
    try:
        loop = asyncio.get_event_loop()
        loop.stop()
        loop.close()
    except RuntimeError:
        pass