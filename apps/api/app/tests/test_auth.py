def test_guest_login_works(client):
    res = client.post("/api/v1/auth/guest")
    assert res.status_code == 200
    assert res.json()["workspace_id"] == "ws_demo"


def test_demo_owner_login_works(client):
    res = client.post("/api/v1/auth/login", json={"email": "demo@taskflow.ai", "password": "demo12345"})
    assert res.status_code == 200
    assert res.json()["workspaces"][0]["role"] == "owner"
