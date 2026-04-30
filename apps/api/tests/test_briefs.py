import uuid

import pytest

from apps.api.tests.conftest import needs_postgres

TENANT = str(uuid.uuid4())


@needs_postgres
@pytest.mark.anyio
async def test_create_brief_and_check_status(client):
    headers = {"X-Tenant-ID": TENANT}
    resp = await client.post(
        "/api/projects",
        json={"name": "Brief Test"},
        headers=headers,
    )
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    resp = await client.post(
        "/api/briefs",
        json={
            "project_id": project_id,
            "natural_language": "Find the top 5 Python frameworks",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    brief_id = data["id"]

    resp = await client.get(f"/api/runs/{brief_id}", headers=headers)
    assert resp.status_code == 200
