import socket

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from inndxd_api.main import create_app


def _postgres_available():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        s.connect(("localhost", 5432))
        return True
    except Exception:
        return False
    finally:
        s.close()


POSTGRES_AVAILABLE = _postgres_available()

needs_postgres = pytest.mark.skipif(
    not POSTGRES_AVAILABLE,
    reason="PostgreSQL not available on localhost:5432",
)


@pytest_asyncio.fixture
async def client():
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=True,
    ) as ac:
        yield ac
