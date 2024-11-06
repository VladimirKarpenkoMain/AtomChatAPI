import asyncio
import json
from datetime import datetime

import pytest
from gunicorn.util import write
from sqlalchemy import insert

from app.core.database import Base, engine, async_session_maker
from app.core.config import settings
from app.chat.models import Message
from app.auth.models import User
from app.auth.models import Blocked
from app.main import app as fastapi_app

from fastapi.testclient import TestClient
from httpx import AsyncClient


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    assert settings.MODE == 'TEST'

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    def open_mock_json(model: str):
        with open(f"app/tests/mock_{model}.json", "r") as file:
            return json.load(file)

    users = open_mock_json("users")
    messages = open_mock_json("messages")
    blocked = open_mock_json("blocked")

    for message in messages:
        message["created_at"] = datetime.strptime(message.get("created_at"), "%Y-%m-%dT%H:%M:%SZ")

    async with async_session_maker() as session:
        add_users = insert(User).values(users)
        add_messages = insert(Message).values(messages)
        add_blocked = insert(Blocked).values(blocked)

        await session.execute(add_users)
        await session.execute(add_messages)
        await session.execute(add_blocked)

        await session.commit()

@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def ac():
    async with AsyncClient(app=fastapi_app, base_url="http://test") as ac:
        yield ac

# @pytest.fixture(scope="function")
# async def session():
#     async with async_session_maker() as session:
#         yield session
