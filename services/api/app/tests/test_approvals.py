def test_approval_rejection_stops_run(client, guest_headers):
    started = client.post("/api/v1/workspaces/ws_demo/workflows/wf_competitor/runs", headers=guest_headers, json={"input": {"query": "Research Bytebase and wait for rejection."}})
    run_id = started.json()["run_id"]
    detail = client.get(f"/api/v1/workspaces/ws_demo/runs/{run_id}", headers=guest_headers).json()
    approval_id = detail["approvals"][0]["id"]

    rejected = client.post(f"/api/v1/workspaces/ws_demo/approvals/{approval_id}/reject", headers=guest_headers, json={"decision_note": "reject"})
    assert rejected.status_code == 200
    assert rejected.json()["run"]["status"] == "failed"
