from app.db.session import SessionLocal
from app.models.entities import AgentRunStep, ToolCall, UsageLog


def start_demo_run(client, headers, query="Research Bytebase and create a short outreach brief.", extra=None):
    payload = {"query": query}
    if extra:
        payload.update(extra)
    res = client.post("/api/v1/workspaces/ws_demo/workflows/wf_competitor/runs", headers=headers, json={"input": payload})
    assert res.status_code == 200
    return res.json()["run_id"], res.json()


def run_detail(client, headers, run_id):
    res = client.get(f"/api/v1/workspaces/ws_demo/runs/{run_id}", headers=headers)
    assert res.status_code == 200
    return res.json()


def approve_pending(client, headers, detail):
    approval_id = detail["approvals"][0]["id"]
    res = client.post(f"/api/v1/workspaces/ws_demo/approvals/{approval_id}/approve", headers=headers, json={"decision_note": "approved by test"})
    assert res.status_code == 200
    return res.json()


def test_successful_workflow_completes_through_graph(client, guest_headers):
    run_id, _ = start_demo_run(client, guest_headers)
    waiting = run_detail(client, guest_headers, run_id)
    assert waiting["run"]["status"] == "waiting_for_approval"
    approve_pending(client, guest_headers, waiting)
    final = run_detail(client, guest_headers, run_id)

    assert final["run"]["id"] == run_id
    assert final["run"]["status"] == "completed"
    assert final["run"]["final_output_json"]["title"] == "Competitor Research & Outreach Brief"
    step_ids = [step["step_id"] for step in final["steps"]]
    for required in ["load_workflow", "validate_permissions", "initialize_run", "plan", "research", "enrich", "approval", "draft", "review", "final"]:
        assert required in step_ids


def test_approval_pause_resume_same_run_and_reject_path(client, guest_headers):
    run_id, _ = start_demo_run(client, guest_headers)
    waiting = run_detail(client, guest_headers, run_id)
    assert waiting["run"]["status"] == "waiting_for_approval"
    assert waiting["approvals"][0]["status"] == "pending"

    approved = approve_pending(client, guest_headers, waiting)
    assert approved["run"]["id"] == run_id
    assert approved["run"]["status"] == "completed"

    rejected_run_id, _ = start_demo_run(client, guest_headers, "Research Bytebase for rejection.")
    rejected_waiting = run_detail(client, guest_headers, rejected_run_id)
    approval_id = rejected_waiting["approvals"][0]["id"]
    reject = client.post(f"/api/v1/workspaces/ws_demo/approvals/{approval_id}/reject", headers=guest_headers, json={"decision_note": "no"})
    assert reject.status_code == 200
    rejected = run_detail(client, guest_headers, rejected_run_id)
    assert rejected["run"]["status"] == "failed"
    assert rejected["run"]["error_json"]["code"] == "approval_rejected"


def test_tool_call_executed_from_graph_node_and_usage_created(client, guest_headers):
    run_id, _ = start_demo_run(client, guest_headers)
    detail = run_detail(client, guest_headers, run_id)
    tool_names = {call["tool_name"] for call in detail["tool_calls"]}
    assert "Demo Search" in tool_names
    assert "Company Profile Lookup" in tool_names

    db = SessionLocal()
    try:
        assert db.query(UsageLog).filter_by(run_id=run_id, event_type="tool_call").count() >= 2
        assert db.query(AgentRunStep).filter_by(run_id=run_id, step_id="research", status="completed").first()
    finally:
        db.close()


def test_invalid_tool_input_reaches_error_handler(client, guest_headers):
    run_id, body = start_demo_run(client, guest_headers, "invalid tool input")
    assert body["status"] == "failed"
    detail = run_detail(client, guest_headers, run_id)
    assert detail["run"]["status"] == "failed"
    assert detail["run"]["error_json"]["code"] == "tool_failed"
    assert any(step["step_id"] == "error_handler" for step in detail["steps"])


def test_tool_retry_works(client, guest_headers):
    run_id, _ = start_demo_run(client, guest_headers, "Research Bytebase retry once.")
    detail = run_detail(client, guest_headers, run_id)
    retry_calls = [call for call in detail["tool_calls"] if call["tool_name"] == "Demo Search"]
    assert retry_calls
    assert retry_calls[0]["retry_count"] == 1
    assert retry_calls[0]["status"] == "completed"


def test_max_steps_and_max_cost_stop_run(client, guest_headers):
    steps_run_id, _ = start_demo_run(client, guest_headers, "Research Bytebase.", {"_demo_max_steps": 1})
    steps_detail = run_detail(client, guest_headers, steps_run_id)
    assert steps_detail["run"]["status"] == "failed"
    assert steps_detail["run"]["error_json"]["code"] == "max_steps_exceeded"

    cost_run_id, _ = start_demo_run(client, guest_headers, "Research Bytebase.", {"_demo_max_cost": 1})
    cost_detail = run_detail(client, guest_headers, cost_run_id)
    assert cost_detail["run"]["status"] == "failed"
    assert cost_detail["run"]["error_json"]["code"] == "max_cost_exceeded"
    assert cost_detail["run"]["credits_used"] == 0


def test_final_output_usage_and_credits_are_saved(client, guest_headers):
    run_id, _ = start_demo_run(client, guest_headers)
    waiting = run_detail(client, guest_headers, run_id)
    approve_pending(client, guest_headers, waiting)
    final = run_detail(client, guest_headers, run_id)
    assert final["run"]["final_output_json"]
    assert final["run"]["credits_used"] > 0
    assert final["run"]["prompt_tokens"] > 0
    assert final["run"]["completion_tokens"] > 0

    db = SessionLocal()
    try:
        assert db.query(UsageLog).filter_by(run_id=run_id, event_type="model_call").count() >= 2
        assert db.query(ToolCall).filter_by(run_id=run_id, status="completed").count() >= 2
    finally:
        db.close()
