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


def pytest_configure(config):
    config.addinivalue_line("markers", "db: mark test as requiring a PostgreSQL database")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-db", False) or POSTGRES_AVAILABLE:
        return
    skip_db = pytest.mark.skip(reason="Postgres not available; use --run-db to force")
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip_db)


def pytest_addoption(parser):
    parser.addoption(
        "--run-db",
        action="store_true",
        default=False,
        help="Run tests that require a PostgreSQL database",
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
