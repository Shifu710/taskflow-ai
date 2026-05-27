def test_guest_cannot_edit_tools_but_can_view_manifest(client, guest_headers):
    manifest = client.get("/api/v1/workspaces/ws_demo/mcp/tools", headers=guest_headers)
    assert manifest.status_code == 200
    blocked = client.post("/api/v1/workspaces/ws_demo/mcp/tools/webhook_sender_demo/invoke", headers=guest_headers, json={"payload": {}})
    assert blocked.status_code == 403
