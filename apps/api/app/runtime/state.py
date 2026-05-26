from typing import Any, TypedDict


class AgentRunState(TypedDict, total=False):
    run_id: str
    workspace_id: str
    workflow_id: str
    workflow_version: int
    user_id: str
    role: str
    input: dict
    workflow_definition: dict[str, Any]
    current_step_id: str | None
    status: str
    plan: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    approvals: list[dict[str, Any]]
    messages: list[dict[str, Any]]
    final_output: dict | None
    error: dict | None
    cost: dict[str, Any]
    limits: dict[str, Any]
    trace_id: str | None
    next_action: str | None
    resume_approved: bool
