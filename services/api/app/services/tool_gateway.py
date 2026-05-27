import time
import uuid
from datetime import datetime
from jsonschema import validate, ValidationError
from sqlalchemy.orm import Session

from app.models.entities import Tool, ToolCall, UsageLog
from app.tools.demo_tools import TOOL_FUNCTIONS


def list_manifest(db: Session, workspace_id: str, guest_safe: bool = False) -> dict:
    tools = db.query(Tool).filter_by(workspace_id=workspace_id, enabled=True).all()
    safe_tools = []
    for tool in tools:
        if guest_safe and tool.slug not in {"demo_search", "company_profile_lookup", "calculator", "csv_analyzer", "email_draft_generator", "task_creator_demo", "webhook_sender_demo"}:
            continue
        safe_tools.append({"name": tool.slug, "description": tool.description, "input_schema": tool.input_schema})
    return {"tools": safe_tools}


def invoke_tool(db: Session, workspace_id: str, tool_slug: str, payload: dict, run_id: str | None = None, step_id: str | None = None) -> dict:
    tool = db.query(Tool).filter_by(workspace_id=workspace_id, slug=tool_slug, enabled=True).first()
    if not tool:
        raise ValueError(f"Tool {tool_slug} not found or disabled")
    try:
        validate(payload, tool.input_schema)
    except ValidationError as exc:
        raise ValueError(f"Invalid tool input: {exc.message}") from exc

    started = datetime.utcnow()
    start = time.perf_counter()
    retry_count = 0
    last_error = None
    output = None
    status = "failed"
    for attempt in range(tool.max_retries + 1):
        retry_count = attempt
        try:
            output = TOOL_FUNCTIONS[tool.slug](payload)
            if tool.output_schema:
                validate(output, tool.output_schema)
            status = "completed"
            last_error = None
            break
        except Exception as exc:  # demo runtime needs to record visible retries
            last_error = str(exc)
            status = "failed"
    latency_ms = int((time.perf_counter() - start) * 1000)
    call = ToolCall(
        id=str(uuid.uuid4()),
        run_id=run_id,
        step_id=step_id,
        tool_id=tool.id,
        tool_name=tool.name,
        input_json=payload,
        output_json=output,
        status=status,
        error_message=last_error,
        latency_ms=latency_ms,
        retry_count=retry_count,
        started_at=started,
        finished_at=datetime.utcnow(),
    )
    db.add(call)
    db.add(UsageLog(
        id=str(uuid.uuid4()),
        workspace_id=workspace_id,
        run_id=run_id,
        event_type="tool_call",
        provider="internal-mcp-style-gateway",
        model="tool",
        tool_slug=tool.slug,
        credits_used=0.25,
        latency_ms=latency_ms,
    ))
    db.commit()
    if status != "completed":
        raise ValueError(last_error or "Tool failed")
    return {"tool_call_id": call.id, "output": output, "latency_ms": latency_ms, "retry_count": retry_count}
