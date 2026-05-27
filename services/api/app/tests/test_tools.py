def test_tool_schema_validation_rejects_invalid_input(client, guest_headers):
    res = client.post("/api/v1/workspaces/ws_demo/mcp/tools/demo_search/invoke", headers=guest_headers, json={})
    assert res.status_code == 400


def test_valid_tool_invocation_logs_usage(client, guest_headers):
    res = client.post("/api/v1/workspaces/ws_demo/mcp/tools/demo_search/invoke", headers=guest_headers, json={"query": "Bytebase"})
    assert res.status_code == 200
    usage = client.get("/api/v1/workspaces/ws_demo/usage", headers=guest_headers)
    assert any(row["event_type"] == "tool_call" for row in usage.json()["usage_logs"])
