
import pytest
from httpx import ASGITransport, AsyncClient
from inndxd_api.main import create_app


@pytest.mark.asyncio
async def test_get_run_status_not_found():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/runs/00000000-0000-0000-0000-000000000001",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        assert response.status_code == 404
