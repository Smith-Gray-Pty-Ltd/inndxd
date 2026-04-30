import uuid

import pytest

TENANT = str(uuid.uuid4())


@pytest.mark.anyio
@pytest.mark.db
async def test_create_and_list_projects(client):
    headers = {"X-Tenant-ID": TENANT}
    resp = await client.post(
        "/api/projects",
        json={"name": "Test"},
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test"
    project_id = data["id"]

    resp = await client.get("/api/projects", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["projects"]) >= 1

    resp = await client.delete(f"/api/projects/{project_id}", headers=headers)
    assert resp.status_code == 204
