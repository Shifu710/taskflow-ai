def test_webhook_secret_required(client):
    res = client.post("/api/v1/workspaces/ws_demo/workflows/wf_competitor/webhook", json={"query": "Bytebase"})
    assert res.status_code == 401
