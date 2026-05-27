import time
import uuid
from datetime import datetime
from jsonschema import validate
from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.db.seed import DEMO_WORKFLOW_ID
from app.models.entities import AgentRun, AgentRunStep, Approval, CreditTransaction, UsageLog, Workflow, Workspace
from app.runtime.model_gateway import model_gateway
from app.runtime.state import AgentRunState
from app.services.rbac import role_for
from app.services.tool_gateway import invoke_tool

FINAL_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "findings": {"type": "array", "items": {"type": "string"}},
        "recommended_actions": {"type": "array", "items": {"type": "string"}},
        "draft_message": {"type": "string"},
        "risks": {"type": "array", "items": {"type": "string"}},
        "sources": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "summary", "findings", "recommended_actions", "draft_message", "risks", "sources"],
}


def create_run(db: Session, workspace_id: str, workflow_id: str, user_id: str, input_json: dict) -> AgentRun:
    run = create_run_record(db, workspace_id, workflow_id, user_id, input_json)
    return execute_until_pause_or_done(db, run.id, approved=False)


def create_run_record(db: Session, workspace_id: str, workflow_id: str, user_id: str, input_json: dict) -> AgentRun:
    workflow = db.query(Workflow).filter_by(id=workflow_id, workspace_id=workspace_id).first()
    if not workflow:
        raise ValueError("Workflow not found")
    run = AgentRun(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        workflow_id=workflow_id,
        workflow_version=workflow.version,
        user_id=user_id,
        status="queued",
        input_json=input_json,
        credits_reserved=10,
        langfuse_trace_id=f"local-{uuid.uuid4()}",
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def execute_until_pause_or_done(db: Session, run_id: str, approved: bool = False) -> AgentRun:
    run = db.query(AgentRun).filter_by(id=run_id).one()
    graph = build_graph(db)
    state: AgentRunState = {
        "run_id": run.id,
        "workspace_id": run.workspace_id,
        "workflow_id": run.workflow_id,
        "workflow_version": run.workflow_version,
        "user_id": run.user_id,
        "input": run.input_json,
        "current_step_id": run.current_step_id,
        "status": run.status,
        "plan": [],
        "tool_results": [],
        "approvals": [],
        "messages": [],
        "final_output": run.final_output_json,
        "error": run.error_json,
        "cost": {"credits": run.credits_used, "tool_calls": run.tool_calls_count},
        "trace_id": run.langfuse_trace_id,
        "resume_approved": approved,
        "next_action": None,
    }
    graph.invoke(state)
    db.expire_all()
    return db.query(AgentRun).filter_by(id=run_id).one()


def build_graph(db: Session):
    graph = StateGraph(AgentRunState)
    graph.add_node("load_workflow", lambda state: load_workflow(db, state))
    graph.add_node("validate_permissions", lambda state: validate_permissions(db, state))
    graph.add_node("initialize_run", lambda state: initialize_run(db, state))
    graph.add_node("planner", lambda state: planner(db, state))
    graph.add_node("tool_router", lambda state: tool_router(db, state))
    graph.add_node("execute_tool", lambda state: execute_tool(db, state))
    graph.add_node("approval_gate", lambda state: approval_gate(db, state))
    graph.add_node("condition_router", lambda state: condition_router(db, state))
    graph.add_node("agent_execute", lambda state: agent_execute(db, state))
    graph.add_node("reviewer", lambda state: reviewer(db, state))
    graph.add_node("finalize", lambda state: finalize(db, state))
    graph.add_node("error_handler", lambda state: error_handler(db, state))

    graph.set_entry_point("load_workflow")
    graph.add_conditional_edges("load_workflow", route_after_node, {"validate_permissions": "validate_permissions", "error_handler": "error_handler"})
    graph.add_conditional_edges("validate_permissions", route_after_node, {"initialize_run": "initialize_run", "error_handler": "error_handler"})
    graph.add_conditional_edges("initialize_run", route_after_node, {"planner": "planner", "error_handler": "error_handler"})
    graph.add_conditional_edges("planner", route_after_node, {"tool_router": "tool_router", "error_handler": "error_handler"})
    graph.add_conditional_edges(
        "tool_router",
        route_after_node,
        {
            "execute_tool": "execute_tool",
            "approval_gate": "approval_gate",
            "agent_execute": "agent_execute",
            "reviewer": "reviewer",
            "finalize": "finalize",
            "error_handler": "error_handler",
        },
    )
    graph.add_conditional_edges("execute_tool", route_after_node, {"condition_router": "condition_router", "error_handler": "error_handler"})
    graph.add_conditional_edges("approval_gate", route_after_node, {"condition_router": "condition_router", "error_handler": "error_handler", "end": END})
    graph.add_conditional_edges("condition_router", route_after_node, {"tool_router": "tool_router", "finalize": "finalize", "error_handler": "error_handler"})
    graph.add_conditional_edges("agent_execute", route_after_node, {"reviewer": "reviewer", "condition_router": "condition_router", "error_handler": "error_handler"})
    graph.add_conditional_edges("reviewer", route_after_node, {"finalize": "finalize", "error_handler": "error_handler"})
    graph.add_edge("finalize", END)
    graph.add_edge("error_handler", END)
    return graph.compile()


def route_after_node(state: AgentRunState) -> str:
    return state.get("next_action") or "error_handler"


def load_workflow(db: Session, state: AgentRunState) -> AgentRunState:
    workflow = db.query(Workflow).filter_by(id=state["workflow_id"], workspace_id=state["workspace_id"]).first()
    if not workflow:
        return set_error(state, "workflow_not_found", "Workflow not found", "load_workflow")
    state["workflow_definition"] = workflow.definition_json
    state["workflow_version"] = workflow.version
    state["next_action"] = "validate_permissions"
    persist_step(db, state["run_id"], "load_workflow", "system", "completed", output_json={"workflow_id": workflow.id, "version": workflow.version})
    return state


def validate_permissions(db: Session, state: AgentRunState) -> AgentRunState:
    try:
        role = "system" if state["user_id"] == "webhook" else role_for(db, state["workspace_id"], state["user_id"])
        if role == "guest" and state["workflow_id"] != DEMO_WORKFLOW_ID:
            return set_error(state, "permission_denied", "Guest can only run the prebuilt demo workflow", "validate_permissions")
        state["role"] = role
        state["next_action"] = "initialize_run"
        persist_step(db, state["run_id"], "validate_permissions", "system", "completed", output_json={"role": role})
        return state
    except Exception as exc:
        return set_error(state, "permission_denied", str(exc), "validate_permissions")


def initialize_run(db: Session, state: AgentRunState) -> AgentRunState:
    run = get_run(db, state)
    workspace = db.query(Workspace).filter_by(id=state["workspace_id"]).one()
    run.status = "running"
    run.started_at = run.started_at or datetime.utcnow()
    run.current_step_id = run.current_step_id or "load_workflow"
    state["status"] = run.status
    state["current_step_id"] = run.current_step_id
    state["limits"] = {
        "max_steps": int(state["input"].get("_demo_max_steps", workspace.max_run_steps)),
        "max_cost": float(state["input"].get("_demo_max_cost", workspace.max_run_cost_credits)),
        "max_tool_calls": int(state["input"].get("_demo_max_tool_calls", workspace.max_tool_calls_per_run)),
        "max_runtime_seconds": workspace.max_runtime_seconds,
    }
    db.commit()
    persist_step(db, run.id, "initialize_run", "system", "completed", output_json={"status": "running", "limits": state["limits"]})
    if limits_exceeded(db, state):
        return state
    state["next_action"] = "planner"
    return state


def planner(db: Session, state: AgentRunState) -> AgentRunState:
    if completed_step(db, state["run_id"], "plan"):
        state["next_action"] = "tool_router"
        return state
    if limits_exceeded(db, state):
        return state
    query = state["input"].get("query", "Research Bytebase and create a short outreach brief.")
    model = model_gateway(query, "planner")
    if would_exceed_cost(db, state, model["credits"], "plan"):
        return state
    plan = [{"step": item["id"], "type": item["type"]} for item in state["workflow_definition"].get("steps", [])]
    state["plan"] = plan
    persist_step(db, state["run_id"], "plan", "planner", "completed", {"query": query}, {"plan": plan, "model": model})
    add_model_usage(db, state, model, "planner")
    charge(db, state, model["credits"], "Planner model call")
    state["next_action"] = "tool_router"
    return state


def tool_router(db: Session, state: AgentRunState) -> AgentRunState:
    if state.get("error"):
        state["next_action"] = "error_handler"
        return state
    if limits_exceeded(db, state):
        return state
    for step in state["workflow_definition"].get("steps", []):
        step_id = step["id"]
        step_type = step["type"]
        if step_type == "tool_call" and not completed_step(db, state["run_id"], step_id):
            state["current_step_id"] = step_id
            state["next_action"] = "execute_tool"
            persist_step(db, state["run_id"], "tool_router", "router", "completed", output_json={"next_step_id": step_id, "route": "execute_tool"})
            return state
        if step_type == "approval" and not approval_resolved(db, state["run_id"], step_id):
            state["current_step_id"] = step_id
            state["next_action"] = "approval_gate"
            persist_step(db, state["run_id"], "tool_router", "router", "completed", output_json={"next_step_id": step_id, "route": "approval_gate"})
            return state
        if step_type == "agent" and not completed_step(db, state["run_id"], step_id):
            state["current_step_id"] = step_id
            state["next_action"] = "agent_execute"
            return state
        if step_type == "reviewer" and not completed_step(db, state["run_id"], step_id):
            state["current_step_id"] = step_id
            state["next_action"] = "reviewer"
            return state
        if step_type == "formatter" and not completed_step(db, state["run_id"], step_id):
            state["current_step_id"] = step_id
            state["next_action"] = "finalize"
            return state
    state["next_action"] = "finalize"
    return state


def execute_tool(db: Session, state: AgentRunState) -> AgentRunState:
    if limits_exceeded(db, state):
        return state
    step = workflow_step(state, state["current_step_id"])
    if not step:
        return set_error(state, "step_not_found", "Tool step not found", "execute_tool")
    tool_slug = step.get("tool")
    if state.get("role") == "guest" and tool_slug not in {"demo_search", "company_profile_lookup", "calculator", "csv_analyzer"}:
        return set_error(state, "unsafe_guest_tool", "Guest cannot execute this tool", step["id"])
    query = state["input"].get("query", "")
    payload = build_tool_payload(step["id"], tool_slug, query)
    started = datetime.utcnow()
    persist_step(db, state["run_id"], step["id"], "tool_call", "running", payload, started_at=started)
    try:
        result = invoke_tool(db, state["workspace_id"], tool_slug, payload, state["run_id"], step["id"])
        persist_step(db, state["run_id"], step["id"], "tool_call", "completed", payload, result, retry_count=result["retry_count"], started_at=started)
        run = get_run(db, state)
        run.tool_calls_count += 1
        db.commit()
        charge(db, state, 0.25, f"Tool call {tool_slug}")
        state.setdefault("tool_results", []).append({"step_id": step["id"], "tool": tool_slug, "result": result})
        state["next_action"] = "condition_router"
        return state
    except Exception as exc:
        persist_step(db, state["run_id"], step["id"], "tool_call", "failed", payload, error_json={"message": str(exc)}, started_at=started)
        return set_error(state, "tool_failed", str(exc), step["id"])


def approval_gate(db: Session, state: AgentRunState) -> AgentRunState:
    step = workflow_step(state, state["current_step_id"])
    step_id = step["id"] if step else "approval"
    approval = db.query(Approval).filter_by(run_id=state["run_id"], step_id=step_id).first()
    run = get_run(db, state)
    if not approval:
        approval = Approval(
            id=str(uuid.uuid4()),
            workspace_id=state["workspace_id"],
            run_id=state["run_id"],
            step_id=step_id,
            requested_by=state["user_id"],
            status="pending",
            message=(step or {}).get("message", "Approve generating outreach brief?"),
            payload_json={"query": state["input"].get("query"), "notice": "Public demo uses seeded data and simulated external writes."},
        )
        db.add(approval)
        run.status = "waiting_for_approval"
        run.current_step_id = step_id
        db.commit()
        persist_step(db, state["run_id"], step_id, "approval", "waiting_for_approval", approval.payload_json, {"approval_id": approval.id})
        state["status"] = "waiting_for_approval"
        state["approvals"] = [{"id": approval.id, "status": approval.status}]
        state["next_action"] = "end"
        return state
    if approval.status == "pending":
        run.status = "waiting_for_approval"
        run.current_step_id = step_id
        db.commit()
        state["status"] = "waiting_for_approval"
        state["next_action"] = "end"
        return state
    if approval.status == "rejected":
        return set_error(state, "approval_rejected", "Human approval rejected", step_id)
    persist_step(db, state["run_id"], step_id, "approval", "completed", approval.payload_json, {"approval_id": approval.id, "decision": "approved"})
    state["approvals"] = [{"id": approval.id, "status": approval.status}]
    state["next_action"] = "condition_router"
    return state


def condition_router(db: Session, state: AgentRunState) -> AgentRunState:
    if limits_exceeded(db, state):
        return state
    persist_step(db, state["run_id"], "condition_router", "router", "completed", output_json={"route": "tool_router"})
    state["next_action"] = "tool_router"
    return state


def agent_execute(db: Session, state: AgentRunState) -> AgentRunState:
    if limits_exceeded(db, state):
        return state
    step_id = state["current_step_id"] or "draft"
    if completed_step(db, state["run_id"], step_id):
        state["next_action"] = "condition_router"
        return state
    query = state["input"].get("query", "")
    model = model_gateway(query, "outreach_writer")
    if would_exceed_cost(db, state, model["credits"], step_id):
        return state
    draft = f"Hi team, I noticed your work around {query}. TaskFlow AI can help automate approved agent workflows with auditable tool calls and usage logs."
    persist_step(db, state["run_id"], step_id, "agent", "completed", {"query": query}, {"draft_message": draft, "model": model})
    add_model_usage(db, state, model, "outreach_writer")
    charge(db, state, model["credits"], "Outreach writer model call")
    state.setdefault("messages", []).append({"role": "agent", "content": draft})
    state["next_action"] = "condition_router"
    return state


def reviewer(db: Session, state: AgentRunState) -> AgentRunState:
    step_id = state["current_step_id"] or "review"
    if not completed_step(db, state["run_id"], step_id):
        output = {"tone": "professional", "missing_fields": [], "hallucination_risk": "low", "note": "Reviewer used seeded demo sources only."}
        persist_step(db, state["run_id"], step_id, "reviewer", "completed", output_json=output)
    state["next_action"] = "finalize"
    return state


def finalize(db: Session, state: AgentRunState) -> AgentRunState:
    run = get_run(db, state)
    if run.status == "completed":
        state["next_action"] = "end"
        return state
    final_output = {
        "title": "Competitor Research & Outreach Brief",
        "summary": "TaskFlow AI researched the target with seeded demo data, paused for approval, generated outreach, and reviewed the result.",
        "findings": ["The target values operational reliability.", "Approval workflows and auditability are strong outreach angles.", "All public-demo external actions are simulated."],
        "recommended_actions": ["Lead with human-in-the-loop controls.", "Mention live execution traces and usage logs.", "Invite a short workflow automation review."],
        "draft_message": "Hi team, I noticed your work in developer operations. TaskFlow AI helps teams run approved AI agent workflows with auditable tool calls, retries, and cost controls. Would a short workflow review be useful?",
        "risks": ["Seeded demo data is not live web research.", "Outreach is a draft and should be reviewed before sending."],
        "sources": ["seeded-demo-data", "demo_search", "company_profile_lookup"],
    }
    try:
        validate(final_output, FINAL_SCHEMA)
    except Exception as exc:
        return set_error(state, "failed_validation", str(exc), "final")
    if not completed_step(db, state["run_id"], "final"):
        persist_step(db, state["run_id"], "final", "formatter", "completed", output_json=final_output)
    run.final_output_json = final_output
    run.status = "completed"
    run.current_step_id = "final"
    run.runtime_ms = runtime_ms(run)
    run.finished_at = datetime.utcnow()
    db.commit()
    state["final_output"] = final_output
    state["status"] = "completed"
    state["next_action"] = "end"
    return state


def error_handler(db: Session, state: AgentRunState) -> AgentRunState:
    run = get_run(db, state)
    error = state.get("error") or {"code": "unknown_error", "message": "Unknown runtime error"}
    run.status = "failed"
    run.error_json = error
    run.current_step_id = error.get("step_id")
    run.runtime_ms = runtime_ms(run)
    run.finished_at = datetime.utcnow()
    db.commit()
    persist_step(db, state["run_id"], "error_handler", "error_handler", "failed", error_json=error)
    state["status"] = "failed"
    state["next_action"] = "end"
    return state


def set_error(state: AgentRunState, code: str, message: str, step_id: str) -> AgentRunState:
    state["error"] = {"code": code, "message": message, "step_id": step_id}
    state["next_action"] = "error_handler"
    return state


def get_run(db: Session, state: AgentRunState) -> AgentRun:
    return db.query(AgentRun).filter_by(id=state["run_id"]).one()


def workflow_step(state: AgentRunState, step_id: str | None) -> dict | None:
    for step in state.get("workflow_definition", {}).get("steps", []):
        if step["id"] == step_id:
            return step
    return None


def completed_step(db: Session, run_id: str, step_id: str) -> bool:
    return db.query(AgentRunStep).filter_by(run_id=run_id, step_id=step_id, status="completed").first() is not None


def approval_resolved(db: Session, run_id: str, step_id: str) -> bool:
    approval = db.query(Approval).filter_by(run_id=run_id, step_id=step_id).first()
    return bool(approval and approval.status == "approved")


def build_tool_payload(step_id: str, tool_slug: str, query: str) -> dict:
    if "invalid tool input" in query.lower():
        return {}
    if tool_slug == "demo_search":
        payload = {"query": query}
        if "retry" in query.lower():
            payload["force_retry_once"] = True
        return payload
    if tool_slug == "company_profile_lookup":
        return {"company": "Bytebase" if "bytebase" in query.lower() else "TaskFlow"}
    return {"payload": {"query": query, "step_id": step_id}}


def persist_step(
    db: Session,
    run_id: str,
    step_id: str,
    step_type: str,
    status: str,
    input_json: dict | None = None,
    output_json: dict | None = None,
    error_json: dict | None = None,
    retry_count: int = 0,
    started_at: datetime | None = None,
) -> AgentRunStep:
    started = started_at or datetime.utcnow()
    finished = None if status in {"running", "waiting_for_approval"} else datetime.utcnow()
    row = AgentRunStep(
        id=str(uuid.uuid4()),
        run_id=run_id,
        step_id=step_id,
        step_type=step_type,
        status=status,
        input_json=input_json,
        output_json=output_json,
        error_json=error_json,
        retry_count=retry_count,
        started_at=started,
        finished_at=finished,
        latency_ms=int((finished - started).total_seconds() * 1000) if finished else 0,
    )
    db.add(row)
    db.commit()
    return row


def add_model_usage(db: Session, state: AgentRunState, model: dict, event_type: str) -> None:
    run = get_run(db, state)
    run.prompt_tokens += model["prompt_tokens"]
    run.completion_tokens += model["completion_tokens"]
    db.add(UsageLog(
        id=str(uuid.uuid4()),
        workspace_id=state["workspace_id"],
        run_id=state["run_id"],
        event_type="model_call",
        provider=model["provider"],
        model=model["model"],
        prompt_tokens=model["prompt_tokens"],
        completion_tokens=model["completion_tokens"],
        credits_used=model["credits"],
        latency_ms=350 if event_type == "planner" else 420,
    ))
    db.commit()


def charge(db: Session, state: AgentRunState, amount: float, reason: str) -> None:
    workspace = db.query(Workspace).filter_by(id=state["workspace_id"]).one()
    run = get_run(db, state)
    workspace.credits_balance = round(workspace.credits_balance - amount, 2)
    run.credits_used = round(run.credits_used + amount, 2)
    db.add(CreditTransaction(id=str(uuid.uuid4()), workspace_id=workspace.id, run_id=run.id, amount=-amount, reason=reason, balance_after=workspace.credits_balance))
    db.commit()
    state["cost"] = {"credits": run.credits_used, "tool_calls": run.tool_calls_count}


def limits_exceeded(db: Session, state: AgentRunState) -> bool:
    run = get_run(db, state)
    limits = state.get("limits", {})
    counted_steps = db.query(AgentRunStep).filter(
        AgentRunStep.run_id == run.id,
        AgentRunStep.step_type.notin_(["system", "router"]),
    ).count()
    if counted_steps >= int(limits.get("max_steps", 9999)):
        set_error(state, "max_steps_exceeded", "Maximum run steps exceeded", run.current_step_id or "limits")
        return True
    if run.credits_used >= float(limits.get("max_cost", 999999)):
        set_error(state, "max_cost_exceeded", "Maximum run cost exceeded", run.current_step_id or "limits")
        return True
    if run.tool_calls_count >= int(limits.get("max_tool_calls", 9999)):
        set_error(state, "max_tool_calls_exceeded", "Maximum tool calls exceeded", run.current_step_id or "limits")
        return True
    return False


def would_exceed_cost(db: Session, state: AgentRunState, amount: float, step_id: str) -> bool:
    run = get_run(db, state)
    if run.credits_used + amount > float(state.get("limits", {}).get("max_cost", 999999)):
        set_error(state, "max_cost_exceeded", "Maximum run cost exceeded", step_id)
        return True
    return False


def runtime_ms(run: AgentRun) -> int:
    if not run.started_at:
        return 0
    return int((time.perf_counter() * 0) + (datetime.utcnow() - run.started_at).total_seconds() * 1000)
