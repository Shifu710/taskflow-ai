def test_guest_can_run_demo_workflow_and_approval_resumes(client, guest_headers):
    started = client.post("/api/v1/workspaces/ws_demo/workflows/wf_competitor/runs", headers=guest_headers, json={"input": {"query": "Research Bytebase and create a short outreach brief."}})
    assert started.status_code == 200
    run_id = started.json()["run_id"]
    detail = client.get(f"/api/v1/workspaces/ws_demo/runs/{run_id}", headers=guest_headers).json()
    assert detail["run"]["status"] == "waiting_for_approval"
    approval_id = detail["approvals"][0]["id"]
    approved = client.post(f"/api/v1/workspaces/ws_demo/approvals/{approval_id}/approve", headers=guest_headers, json={"decision_note": "ok"})
    assert approved.status_code == 200
    final = client.get(f"/api/v1/workspaces/ws_demo/runs/{run_id}", headers=guest_headers).json()
    assert final["run"]["status"] == "completed"
    assert final["run"]["final_output_json"]["title"]


def test_run_replay_creates_new_run(client, guest_headers):
    started = client.post("/api/v1/workspaces/ws_demo/workflows/wf_competitor/runs", headers=guest_headers, json={"input": {"query": "Research Bytebase."}})
    run_id = started.json()["run_id"]
    replay = client.post(f"/api/v1/workspaces/ws_demo/runs/{run_id}/replay", headers=guest_headers)
    assert replay.status_code == 200
    assert replay.json()["run_id"] != run_id
