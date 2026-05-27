import asyncio
import json
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.config import settings
from app.db.seed import DEMO_WORKFLOW_ID, DEMO_WORKSPACE_ID
from app.db.session import get_db
from app.models.entities import AgentRun, AgentRunStep, Approval, Tool, ToolCall, UsageLog, User, WebhookEvent, Workflow, WorkflowVersion, Workspace, WorkspaceMember
from app.runtime.engine import create_run, create_run_record, execute_until_pause_or_done
from app.services.rbac import require_permission, role_for
from app.services.security import create_token, hash_password, verify_password
from app.services.tool_gateway import invoke_tool, list_manifest

router = APIRouter(prefix="/api/v1")


class LoginInput(BaseModel):
    email: str
    password: str


class RegisterInput(BaseModel):
    email: str
    password: str
    name: str
    workspace_name: str = "My TaskFlow Workspace"


class RunInput(BaseModel):
    input: dict = {"query": "Research Bytebase and create a short outreach brief."}


class DecisionInput(BaseModel):
    decision_note: str | None = None


class WorkflowInput(BaseModel):
    name: str
    description: str = ""
    definition_json: dict
    status: str = "draft"


@router.post("/auth/login")
def login(payload: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email).first()
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    memberships = db.query(WorkspaceMember).filter_by(user_id=user.id).all()
    return {"token": create_token(user.id), "user": {"id": user.id, "email": user.email, "name": user.name}, "workspaces": [{"id": item.workspace_id, "role": item.role} for item in memberships]}


@router.post("/auth/register")
def register(payload: RegisterInput, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(id=str(uuid.uuid4()), email=payload.email, name=payload.name, password=hash_password(payload.password))
    workspace = Workspace(id=str(uuid.uuid4()), name=payload.workspace_name, credits_balance=500)
    member = WorkspaceMember(id=str(uuid.uuid4()), workspace_id=workspace.id, user_id=user.id, role="owner")
    db.add_all([user, workspace, member])
    db.commit()
    return {
        "token": create_token(user.id),
        "user": {"id": user.id, "email": user.email, "name": user.name},
        "workspaces": [{"id": workspace.id, "role": "owner"}],
    }


@router.post("/auth/guest")
def guest_login(db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email="guest@taskflow.ai").one()
    return {"token": create_token(user.id), "user": {"id": user.id, "email": user.email, "name": user.name}, "workspace_id": DEMO_WORKSPACE_ID}


@router.get("/workspaces")
def workspaces(user: User = Depends(current_user), db: Session = Depends(get_db)):
    members = db.query(WorkspaceMember).filter_by(user_id=user.id).all()
    rows = []
    for member in members:
        workspace = db.query(Workspace).filter_by(id=member.workspace_id).one()
        rows.append({"id": workspace.id, "name": workspace.name, "role": member.role, "credits_balance": workspace.credits_balance})
    return {"workspaces": rows}


@router.get("/workspaces/{workspace_id}/dashboard")
def dashboard(workspace_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "view_usage")
    runs = db.query(AgentRun).filter_by(workspace_id=workspace_id).all()
    tools = db.query(ToolCall).filter(ToolCall.run_id.in_([run.id for run in runs] or ["none"])).all()
    workspace = db.query(Workspace).filter_by(id=workspace_id).one()
    return {
        "total_runs": len(runs),
        "successful_runs": len([run for run in runs if run.status == "completed"]),
        "failed_runs": len([run for run in runs if run.status == "failed"]),
        "waiting_approvals": db.query(Approval).filter_by(workspace_id=workspace_id, status="pending").count(),
        "credits_balance": workspace.credits_balance,
        "credits_used": round(sum(run.credits_used for run in runs), 2),
        "tool_calls": len(tools),
        "langfuse_enabled": bool(settings.langfuse_public_key and settings.langfuse_secret_key),
    }


@router.get("/workspaces/{workspace_id}/workflows")
def workflows(workspace_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "view_workflows")
    rows = db.query(Workflow).filter_by(workspace_id=workspace_id).all()
    return {"workflows": [{"id": row.id, "name": row.name, "description": row.description, "status": row.status, "version": row.version, "definition_json": row.definition_json} for row in rows]}


@router.post("/workspaces/{workspace_id}/workflows")
def create_workflow(workspace_id: str, payload: WorkflowInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "create_workflow")
    status = payload.status if payload.status in {"draft", "published", "archived"} else "draft"
    workflow = Workflow(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        name=payload.name,
        description=payload.description,
        status=status,
        definition_json=payload.definition_json,
        version=1,
        created_by=user.id,
    )
    db.add(workflow)
    db.add(WorkflowVersion(id=str(uuid.uuid4()), workflow_id=workflow.id, version=1, definition_json=workflow.definition_json))
    db.commit()
    return {"id": workflow.id, "name": workflow.name, "status": workflow.status, "version": workflow.version, "definition_json": workflow.definition_json}


@router.get("/workspaces/{workspace_id}/workflows/{workflow_id}")
def workflow_detail(workspace_id: str, workflow_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "view_workflows")
    row = db.query(Workflow).filter_by(workspace_id=workspace_id, id=workflow_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"id": row.id, "name": row.name, "description": row.description, "status": row.status, "version": row.version, "definition_json": row.definition_json, "guest_read_only": role_for(db, workspace_id, user.id) == "guest"}


@router.patch("/workspaces/{workspace_id}/workflows/{workflow_id}")
def update_workflow(workspace_id: str, workflow_id: str, payload: WorkflowInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "edit_workflow")
    workflow = db.query(Workflow).filter_by(workspace_id=workspace_id, id=workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow.name = payload.name
    workflow.description = payload.description
    workflow.definition_json = payload.definition_json
    workflow.status = payload.status if payload.status in {"draft", "published", "archived"} else workflow.status
    workflow.version += 1
    workflow.updated_at = datetime.utcnow()
    db.add(WorkflowVersion(id=str(uuid.uuid4()), workflow_id=workflow.id, version=workflow.version, definition_json=workflow.definition_json))
    db.commit()
    return {"id": workflow.id, "name": workflow.name, "status": workflow.status, "version": workflow.version, "definition_json": workflow.definition_json}


@router.post("/workspaces/{workspace_id}/workflows/{workflow_id}/publish")
def publish_workflow(workspace_id: str, workflow_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "edit_workflow")
    workflow = db.query(Workflow).filter_by(workspace_id=workspace_id, id=workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow.status = "published"
    workflow.version += 1
    workflow.updated_at = datetime.utcnow()
    db.add(WorkflowVersion(id=str(uuid.uuid4()), workflow_id=workflow.id, version=workflow.version, definition_json=workflow.definition_json))
    db.commit()
    return {"id": workflow.id, "status": workflow.status, "version": workflow.version}


@router.get("/workspaces/{workspace_id}/workflows/{workflow_id}/versions")
def workflow_versions(workspace_id: str, workflow_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "view_workflows")
    if not db.query(Workflow).filter_by(workspace_id=workspace_id, id=workflow_id).first():
        raise HTTPException(status_code=404, detail="Workflow not found")
    rows = db.query(WorkflowVersion).filter_by(workflow_id=workflow_id).order_by(WorkflowVersion.version.desc()).all()
    return {"versions": [{"id": row.id, "version": row.version, "definition_json": row.definition_json, "created_at": row.created_at} for row in rows]}


@router.post("/workspaces/{workspace_id}/workflows/{workflow_id}/runs")
def start_run(workspace_id: str, workflow_id: str, payload: RunInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    role = require_permission(db, workspace_id, user.id, "run_workflow")
    if role == "guest" and workflow_id != DEMO_WORKFLOW_ID:
        raise HTTPException(status_code=403, detail="Guest can only run the prebuilt demo workflow")
    if settings.taskflow_use_celery:
        run = create_run_record(db, workspace_id, workflow_id, user.id, payload.input)
        from app.worker import run_workflow_task

        run_workflow_task.delay(run.id)
    else:
        run = create_run(db, workspace_id, workflow_id, user.id, payload.input)
    return {"run_id": run.id, "status": run.status}


@router.get("/workspaces/{workspace_id}/runs")
def runs(workspace_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "view_usage")
    rows = db.query(AgentRun).filter_by(workspace_id=workspace_id).order_by(AgentRun.created_at.desc()).all()
    return {"runs": [_run(row) for row in rows]}


@router.get("/workspaces/{workspace_id}/runs/{run_id}")
def run_detail(workspace_id: str, run_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "view_usage")
    run = db.query(AgentRun).filter_by(workspace_id=workspace_id, id=run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {"run": _run(run), "steps": [_step(row) for row in db.query(AgentRunStep).filter_by(run_id=run_id).all()], "tool_calls": [_tool_call(row) for row in db.query(ToolCall).filter_by(run_id=run_id).all()], "approvals": [_approval(row) for row in db.query(Approval).filter_by(run_id=run_id).all()]}


@router.get("/workspaces/{workspace_id}/runs/{run_id}/events/stream")
async def run_events(workspace_id: str, run_id: str, request: Request, db: Session = Depends(get_db)):
    async def stream():
        last_count = -1
        while True:
            local_db = next(get_db())
            run = local_db.query(AgentRun).filter_by(workspace_id=workspace_id, id=run_id).first()
            steps = local_db.query(AgentRunStep).filter_by(run_id=run_id).all()
            approvals = local_db.query(Approval).filter_by(run_id=run_id).all()
            tool_calls = local_db.query(ToolCall).filter_by(run_id=run_id).all()
            payload = {"run": _run(run), "steps": [_step(step) for step in steps], "tool_calls": [_tool_call(call) for call in tool_calls], "approvals": [_approval(approval) for approval in approvals]}
            count = len(steps) + len(approvals) + (1 if run and run.status in {"completed", "failed", "waiting_for_approval"} else 0)
            if count != last_count:
                yield f"event: run_update\ndata: {json.dumps(payload, default=str)}\n\n"
                last_count = count
            local_db.close()
            if run and run.status in {"completed", "failed", "cancelled", "expired"}:
                break
            if await request.is_disconnected():
                break
            await asyncio.sleep(1)
    return StreamingResponse(stream(), media_type="text/event-stream")


@router.post("/workspaces/{workspace_id}/runs/{run_id}/replay")
def replay_run(workspace_id: str, run_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "run_workflow")
    old = db.query(AgentRun).filter_by(id=run_id, workspace_id=workspace_id).first()
    if not old:
        raise HTTPException(status_code=404, detail="Run not found")
    run = create_run(db, workspace_id, old.workflow_id, user.id, old.input_json)
    return {"run_id": run.id, "status": run.status}


@router.get("/workspaces/{workspace_id}/approvals")
def approvals(workspace_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "view_usage")
    rows = db.query(Approval).filter_by(workspace_id=workspace_id).order_by(Approval.created_at.desc()).all()
    return {"approvals": [_approval(row) for row in rows]}


@router.post("/workspaces/{workspace_id}/approvals/{approval_id}/approve")
def approve(workspace_id: str, approval_id: str, payload: DecisionInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "approve_demo_action")
    approval = db.query(Approval).filter_by(workspace_id=workspace_id, id=approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    approval.status = "approved"
    approval.approved_by = user.id
    approval.decision_note = payload.decision_note
    approval.decided_at = datetime.utcnow()
    db.commit()
    run = execute_until_pause_or_done(db, approval.run_id, approved=True)
    return {"approval": _approval(approval), "run": _run(run)}


@router.post("/workspaces/{workspace_id}/approvals/{approval_id}/reject")
def reject(workspace_id: str, approval_id: str, payload: DecisionInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "approve_demo_action")
    approval = db.query(Approval).filter_by(workspace_id=workspace_id, id=approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    approval.status = "rejected"
    approval.approved_by = user.id
    approval.decision_note = payload.decision_note
    approval.decided_at = datetime.utcnow()
    db.commit()
    run = execute_until_pause_or_done(db, approval.run_id, approved=False)
    return {"approval": _approval(approval), "run": _run(run)}


@router.get("/workspaces/{workspace_id}/tools")
def tools(workspace_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "view_workflows")
    rows = db.query(Tool).filter_by(workspace_id=workspace_id).all()
    return {"tools": [{"id": row.id, "name": row.name, "slug": row.slug, "description": row.description, "tool_type": row.tool_type, "input_schema": row.input_schema, "enabled": row.enabled, "requires_approval": row.requires_approval, "timeout_seconds": row.timeout_seconds, "max_retries": row.max_retries} for row in rows]}


@router.get("/workspaces/{workspace_id}/mcp/tools")
def mcp_tools(workspace_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    role = require_permission(db, workspace_id, user.id, "view_workflows")
    return list_manifest(db, workspace_id, guest_safe=role == "guest")


@router.post("/workspaces/{workspace_id}/mcp/tools/{tool_slug}/invoke")
def mcp_invoke(workspace_id: str, tool_slug: str, payload: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    role = require_permission(db, workspace_id, user.id, "run_workflow")
    tool = db.query(Tool).filter_by(workspace_id=workspace_id, slug=tool_slug, enabled=True).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    if role == "guest" and tool_slug not in {"demo_search", "company_profile_lookup", "calculator", "email_draft_generator"}:
        raise HTTPException(status_code=403, detail="Guest cannot invoke this tool")
    if tool.requires_approval:
        raise HTTPException(status_code=403, detail="Tool requires a workflow approval gate before invocation")
    try:
        return invoke_tool(db, workspace_id, tool_slug, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/workspaces/{workspace_id}/usage")
def usage(workspace_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    require_permission(db, workspace_id, user.id, "view_usage")
    logs = db.query(UsageLog).filter_by(workspace_id=workspace_id).order_by(UsageLog.created_at.desc()).all()
    return {"usage_logs": [{"id": row.id, "run_id": row.run_id, "event_type": row.event_type, "provider": row.provider, "model": row.model, "tool_slug": row.tool_slug, "credits_used": row.credits_used, "latency_ms": row.latency_ms, "created_at": row.created_at} for row in logs]}


@router.post("/workspaces/{workspace_id}/workflows/{workflow_id}/webhook")
def webhook(workspace_id: str, workflow_id: str, payload: dict, x_taskflow_webhook_secret: str | None = Header(default=None), db: Session = Depends(get_db)):
    if x_taskflow_webhook_secret != settings.webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    db.add(WebhookEvent(id=str(uuid.uuid4()), workspace_id=workspace_id, workflow_id=workflow_id, payload_json=payload, status="received"))
    db.commit()
    run = create_run(db, workspace_id, workflow_id, "webhook", payload)
    return {"received": True, "run_id": run.id}


def _run(row: AgentRun | None) -> dict | None:
    if not row:
        return None
    return {"id": row.id, "workspace_id": row.workspace_id, "workflow_id": row.workflow_id, "status": row.status, "input_json": row.input_json, "final_output_json": row.final_output_json, "error_json": row.error_json, "current_step_id": row.current_step_id, "credits_used": row.credits_used, "prompt_tokens": row.prompt_tokens, "completion_tokens": row.completion_tokens, "tool_calls_count": row.tool_calls_count, "runtime_ms": row.runtime_ms, "trace_id": row.langfuse_trace_id, "created_at": row.created_at, "finished_at": row.finished_at}


def _step(row: AgentRunStep) -> dict:
    return {"id": row.id, "step_id": row.step_id, "step_type": row.step_type, "status": row.status, "input_json": row.input_json, "output_json": row.output_json, "error_json": row.error_json, "retry_count": row.retry_count, "latency_ms": row.latency_ms, "started_at": row.started_at, "finished_at": row.finished_at}


def _tool_call(row: ToolCall) -> dict:
    return {"id": row.id, "step_id": row.step_id, "tool_name": row.tool_name, "input_json": row.input_json, "output_json": row.output_json, "status": row.status, "error_message": row.error_message, "latency_ms": row.latency_ms, "retry_count": row.retry_count}


def _approval(row: Approval) -> dict:
    return {"id": row.id, "run_id": row.run_id, "step_id": row.step_id, "status": row.status, "message": row.message, "payload_json": row.payload_json, "decision_note": row.decision_note, "created_at": row.created_at, "decided_at": row.decided_at}
