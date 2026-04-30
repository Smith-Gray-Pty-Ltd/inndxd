import uuid

import pytest

from apps.api.tests.conftest import needs_postgres

TENANT = str(uuid.uuid4())


@needs_postgres
@pytest.mark.anyio
async def test_list_data_items_empty(client):
    headers = {"X-Tenant-ID": TENANT}
    resp = await client.get("/api/data-items", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "data_items" in data
    assert data["data_items"] == []
