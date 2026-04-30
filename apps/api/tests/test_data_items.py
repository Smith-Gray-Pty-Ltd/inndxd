import uuid

import pytest

TENANT = str(uuid.uuid4())


@pytest.mark.anyio
@pytest.mark.db
async def test_list_data_items_empty(client):
    headers = {"X-Tenant-ID": TENANT}
    resp = await client.get("/api/data-items", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "data_items" in data
    assert data["data_items"] == []
