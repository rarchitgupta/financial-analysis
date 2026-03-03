import os
import pytest
import uuid
import asyncio
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlmodel import SQLModel
from sqlmodel.pool import StaticPool

from app.main import app
from app.db import User, get_session
from app.users import current_active_user


@pytest.fixture
def test_engine_sync():
    async def _create_engine():
        engine: AsyncEngine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        return engine

    loop = asyncio.new_event_loop()
    engine = loop.run_until_complete(_create_engine())

    yield engine

    loop.run_until_complete(engine.dispose())
    loop.close()


@pytest.fixture
async def test_session(test_engine_sync):
    async_session_local = async_sessionmaker(
        test_engine_sync,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_local() as session:
        yield session


@pytest.fixture
def session_mock():
    from unittest.mock import AsyncMock

    from app.services import alphavantage

    alphavantage._cache.clear()

    yield AsyncMock()

    alphavantage._cache.clear()


@pytest.fixture
def test_user():
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
        is_superuser=False,
    )
    return user


@pytest.fixture
def client(test_engine_sync, test_user):
    from app.services import alphavantage

    alphavantage._cache.clear()

    async_session_local = async_sessionmaker(
        test_engine_sync,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def get_test_session():
        async with async_session_local() as session:
            yield session

    def get_test_user():
        return test_user

    app.dependency_overrides[get_session] = get_test_session
    app.dependency_overrides[current_active_user] = get_test_user

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()
    alphavantage._cache.clear()


@pytest.fixture
def client_unauthenticated(test_engine_sync):
    from app.services import alphavantage

    alphavantage._cache.clear()

    async_session_local = async_sessionmaker(
        test_engine_sync,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def get_test_session():
        async with async_session_local() as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    test_client = TestClient(app)
    yield test_client

    app.dependency_overrides.clear()
    alphavantage._cache.clear()


@pytest.fixture
def mock_api_key():
    with patch.dict(os.environ, {"ALPHAVANTAGE_API_KEY": "test_key"}):
        yield "test_key"


@pytest.fixture
def mock_quote_response():
    return {
        "Global Quote": {
            "01. symbol": "AAPL",
            "05. price": "150.25",
            "07. latest trading day": "2025-01-24",
        }
    }


@pytest.fixture
def mock_history_response():
    return {
        "Time Series (Daily)": {
            "2025-01-24": {
                "1. open": "149.50",
                "2. high": "151.00",
                "3. low": "149.50",
                "4. close": "150.25",
            },
            "2025-01-23": {
                "1. open": "148.75",
                "2. high": "150.00",
                "3. low": "148.50",
                "4. close": "149.75",
            },
        }
    }


@pytest.fixture
def mock_search_response():
    return {
        "bestMatches": [
            {
                "1. symbol": "AAPL",
                "2. name": "Apple Inc.",
                "3. type": "Equity",
                "4. region": "United States",
            },
            {
                "1. symbol": "AAPL.L",
                "2. name": "Apple Inc.",
                "3. type": "Equity",
                "4. region": "United Kingdom",
            },
        ]
    }
