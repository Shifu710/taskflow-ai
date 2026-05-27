def owner_headers(client):
    res = client.post("/api/v1/auth/login", json={"email": "demo@taskflow.ai", "password": "demo12345"})
    token = res.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_owner_workspace(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "founder@example.com", "password": "strongpass123", "name": "Founder", "workspace_name": "Founder Workspace"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["workspaces"][0]["role"] == "owner"


def test_seeded_workflows_are_two_required_templates(client, guest_headers):
    res = client.get("/api/v1/workspaces/ws_demo/workflows", headers=guest_headers)
    assert res.status_code == 200
    names = {row["name"] for row in res.json()["workflows"]}
    assert names == {"Competitor Research & Outreach Agent", "Customer Support Triage Agent"}


def test_owner_can_create_publish_and_view_versions(client):
    headers = owner_headers(client)
    definition = {
        "name": "Owner Draft",
        "trigger": {"type": "manual"},
        "steps": [{"id": "plan", "type": "planner"}, {"id": "final", "type": "formatter"}],
    }
    created = client.post(
        "/api/v1/workspaces/ws_demo/workflows",
        headers=headers,
        json={"name": "Owner Draft", "description": "Draft workflow", "definition_json": definition, "status": "draft"},
    )
    assert created.status_code == 200
    workflow_id = created.json()["id"]

    published = client.post(f"/api/v1/workspaces/ws_demo/workflows/{workflow_id}/publish", headers=headers)
    assert published.status_code == 200
    assert published.json()["status"] == "published"

    versions = client.get(f"/api/v1/workspaces/ws_demo/workflows/{workflow_id}/versions", headers=headers)
    assert versions.status_code == 200
    assert len(versions.json()["versions"]) == 2


def test_guest_cannot_create_workflow(client, guest_headers):
    res = client.post(
        "/api/v1/workspaces/ws_demo/workflows",
        headers=guest_headers,
        json={"name": "Blocked", "description": "", "definition_json": {"steps": []}, "status": "draft"},
    )
    assert res.status_code == 403
