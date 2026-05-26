def test_successful_run_deducts_credits_and_failed_limit_run_does_not_overcharge(client, guest_headers):
    before = client.get("/api/v1/workspaces/ws_demo/dashboard", headers=guest_headers).json()["credits_balance"]
    started = client.post("/api/v1/workspaces/ws_demo/workflows/wf_competitor/runs", headers=guest_headers, json={"input": {"query": "Research Bytebase."}})
    run_id = started.json()["run_id"]
    detail = client.get(f"/api/v1/workspaces/ws_demo/runs/{run_id}", headers=guest_headers).json()
    approval_id = detail["approvals"][0]["id"]
    client.post(f"/api/v1/workspaces/ws_demo/approvals/{approval_id}/approve", headers=guest_headers, json={"decision_note": "ok"})
    after_success = client.get("/api/v1/workspaces/ws_demo/dashboard", headers=guest_headers).json()["credits_balance"]
    assert after_success < before

    failed = client.post("/api/v1/workspaces/ws_demo/workflows/wf_competitor/runs", headers=guest_headers, json={"input": {"query": "Research Bytebase.", "_demo_max_cost": 1}})
    failed_id = failed.json()["run_id"]
    failed_detail = client.get(f"/api/v1/workspaces/ws_demo/runs/{failed_id}", headers=guest_headers).json()
    assert failed_detail["run"]["status"] == "failed"
    assert failed_detail["run"]["credits_used"] == 0
