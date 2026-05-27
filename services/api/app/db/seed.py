import uuid

from sqlalchemy.orm import Session

from app.models.entities import (
    AgentRun,
    Approval,
    CreditTransaction,
    ScheduledTrigger,
    Tool,
    UsageLog,
    User,
    WebhookEvent,
    Workflow,
    WorkflowVersion,
    Workspace,
    WorkspaceMember,
)
from app.services.security import hash_password

DEMO_WORKSPACE_ID = "ws_demo"
GUEST_USER_ID = "usr_guest"
DEMO_USER_ID = "usr_demo"
DEMO_WORKFLOW_ID = "wf_competitor"


COMPETITOR_WORKFLOW = {
    "name": "Competitor Research & Outreach Agent",
    "trigger": {"type": "manual"},
    "steps": [
        {"id": "plan", "type": "planner", "max_retries": 0},
        {"id": "research", "type": "tool_call", "tool": "demo_search", "max_retries": 1},
        {"id": "enrich", "type": "tool_call", "tool": "company_profile_lookup", "max_retries": 1},
        {"id": "approval", "type": "approval", "message": "Approve generating outreach brief?"},
        {"id": "draft", "type": "agent", "agent": "outreach_writer"},
        {"id": "review", "type": "reviewer"},
        {"id": "final", "type": "formatter"},
    ],
}

SUPPORT_TRIAGE_WORKFLOW = {
    "name": "Customer Support Triage Agent",
    "trigger": {"type": "manual"},
    "steps": [
        {"id": "plan", "type": "planner", "max_retries": 0},
        {"id": "classify", "type": "agent", "agent": "support_classifier"},
        {"id": "faq_lookup", "type": "tool_call", "tool": "demo_search", "max_retries": 1},
        {"id": "draft_reply", "type": "tool_call", "tool": "email_draft_generator", "max_retries": 1},
        {"id": "approval", "type": "approval", "message": "Approve the drafted support response?"},
        {"id": "create_ticket", "type": "tool_call", "tool": "create_ticket_demo", "max_retries": 1},
        {"id": "review", "type": "reviewer"},
        {"id": "final", "type": "formatter"},
    ],
}


def tool_schema(slug: str) -> tuple[dict, dict | None]:
    schemas = {
        "demo_search": ({"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}, None),
        "company_profile_lookup": ({"type": "object", "properties": {"company": {"type": "string"}}, "required": ["company"]}, None),
        "calculator": ({"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}, None),
        "email_draft_generator": ({"type": "object", "properties": {"payload": {"type": "object"}}, "required": ["payload"]}, None),
        "create_ticket_demo": ({"type": "object", "properties": {"payload": {"type": "object"}}, "required": ["payload"]}, None),
        "task_creator_demo": ({"type": "object", "properties": {"payload": {"type": "object"}}, "required": ["payload"]}, None),
        "webhook_sender_demo": ({"type": "object", "properties": {"payload": {"type": "object"}}, "required": ["payload"]}, None),
    }
    return schemas.get(slug, ({"type": "object", "properties": {"payload": {"type": "object"}}, "required": ["payload"]}, None))


def seed_database(db: Session) -> None:
    if db.query(Workspace).filter_by(id=DEMO_WORKSPACE_ID).first():
        return

    # Recover from a partial seed where demo users exist without the demo workspace.
    db.query(User).filter(User.id.in_([GUEST_USER_ID, DEMO_USER_ID])).delete(synchronize_session=False)
    db.commit()

    guest = User(id=GUEST_USER_ID, email="guest@taskflow.ai", name="Guest Demo", password=hash_password("guest123"))
    demo = User(id=DEMO_USER_ID, email="demo@taskflow.ai", name="Demo Owner", password=hash_password("demo12345"))
    workspace = Workspace(id=DEMO_WORKSPACE_ID, name="TaskFlow Demo Workspace", credits_balance=1000)
    db.add_all([
        guest,
        demo,
        workspace,
        WorkspaceMember(id=str(uuid.uuid4()), workspace_id=DEMO_WORKSPACE_ID, user_id=GUEST_USER_ID, role="guest"),
        WorkspaceMember(id=str(uuid.uuid4()), workspace_id=DEMO_WORKSPACE_ID, user_id=DEMO_USER_ID, role="owner"),
    ])
    db.flush()

    workflow = Workflow(
        id=DEMO_WORKFLOW_ID,
        workspace_id=DEMO_WORKSPACE_ID,
        name="Competitor Research & Outreach Agent",
        description="Plans research, invokes demo tools, pauses for human approval, writes outreach, reviews risk, and formats a structured report.",
        status="published",
        definition_json=COMPETITOR_WORKFLOW,
        version=1,
        created_by=DEMO_USER_ID,
    )
    db.add(workflow)
    db.add(WorkflowVersion(id=str(uuid.uuid4()), workflow_id=workflow.id, version=1, definition_json=COMPETITOR_WORKFLOW))

    support_workflow = Workflow(
        id="wf_support_triage",
        workspace_id=DEMO_WORKSPACE_ID,
        name="Customer Support Triage Agent",
        description="Classifies support requests, drafts a support reply, pauses for approval, and simulates ticket creation.",
        status="published",
        definition_json=SUPPORT_TRIAGE_WORKFLOW,
        version=1,
        created_by=DEMO_USER_ID,
    )
    db.add(support_workflow)
    db.add(WorkflowVersion(id=str(uuid.uuid4()), workflow_id=support_workflow.id, version=1, definition_json=SUPPORT_TRIAGE_WORKFLOW))

    for slug in [
        "demo_search",
        "company_profile_lookup",
        "calculator",
        "email_draft_generator",
        "create_ticket_demo",
        "task_creator_demo",
        "webhook_sender_demo",
    ]:
        input_schema, output_schema = tool_schema(slug)
        db.add(Tool(
            id=f"tool_{slug}",
            workspace_id=DEMO_WORKSPACE_ID,
            name=slug.replace("_", " ").title(),
            slug=slug,
            description=f"Demo-safe {slug.replace('_', ' ')} tool. External writes are simulated in public demo mode.",
            tool_type="demo" if slug.endswith("_demo") or slug in {"demo_search", "company_profile_lookup"} else "utility",
            input_schema=input_schema,
            output_schema=output_schema,
            enabled=True,
            requires_approval=slug in {"webhook_sender_demo", "create_ticket_demo", "task_creator_demo"},
            timeout_seconds=10,
            max_retries=1,
        ))

    completed = AgentRun(
        id="run_completed_seed",
        workspace_id=DEMO_WORKSPACE_ID,
        workflow_id=DEMO_WORKFLOW_ID,
        workflow_version=1,
        user_id=DEMO_USER_ID,
        status="completed",
        input_json={"query": "Research Bytebase and create a short outreach brief."},
        final_output_json={"title": "Bytebase Outreach Brief", "summary": "Seeded completed run.", "findings": ["Approval controls matter."], "recommended_actions": ["Open with operational reliability."], "draft_message": "Hi Bytebase team...", "risks": ["Seeded demo data only."], "sources": ["seeded-demo-data"]},
        credits_used=7.5,
        tool_calls_count=2,
        runtime_ms=4200,
    )
    waiting = AgentRun(
        id="run_waiting_seed",
        workspace_id=DEMO_WORKSPACE_ID,
        workflow_id=DEMO_WORKFLOW_ID,
        workflow_version=1,
        user_id=GUEST_USER_ID,
        status="waiting_for_approval",
        input_json={"query": "Research TaskFlow AI and create a short outreach brief."},
        current_step_id="approval",
        credits_used=3.25,
        tool_calls_count=2,
    )
    failed_retry = AgentRun(
        id="run_retry_seed",
        workspace_id=DEMO_WORKSPACE_ID,
        workflow_id=DEMO_WORKFLOW_ID,
        workflow_version=1,
        user_id=DEMO_USER_ID,
        status="completed",
        input_json={"query": "Show failed tool followed by retry success."},
        final_output_json={"title": "Retry Demo", "summary": "A seeded run records retry recovery.", "findings": ["Retry recovered the tool call."], "recommended_actions": ["Inspect tool logs."], "draft_message": "Retry-safe automation note.", "risks": ["Seeded demo run."], "sources": ["tool-call-log"]},
        credits_used=8.0,
        tool_calls_count=3,
    )
    db.add_all([completed, waiting, failed_retry])
    db.add(Approval(id="appr_seed", workspace_id=DEMO_WORKSPACE_ID, run_id=waiting.id, step_id="approval", requested_by=GUEST_USER_ID, status="pending", message="Approve generating outreach brief?", payload_json={"planned_message": "Generate outreach using seeded demo data."}))
    db.add(ScheduledTrigger(id="sched_demo", workflow_id=DEMO_WORKFLOW_ID, cron_expression="0 9 * * MON", timezone="Asia/Singapore", enabled=False))
    db.add(WebhookEvent(id="webhook_seed", workspace_id=DEMO_WORKSPACE_ID, workflow_id=DEMO_WORKFLOW_ID, payload_json={"demo": True}, status="received"))
    db.add(UsageLog(id=str(uuid.uuid4()), workspace_id=DEMO_WORKSPACE_ID, run_id=completed.id, event_type="model_call", provider="demo-local", model="demo-local", prompt_tokens=900, completion_tokens=420, credits_used=5.0, latency_ms=500))
    db.add(CreditTransaction(id=str(uuid.uuid4()), workspace_id=DEMO_WORKSPACE_ID, run_id=completed.id, amount=-7.5, reason="Seeded completed agent run", balance_after=992.5))
    db.commit()
