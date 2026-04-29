import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from inndxd_api.main import app
from inndxd_core.db import engine
from inndxd_core.models.base import Base


@pytest_asyncio.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
