import Link from "next/link";

const sections = [
  ["What this project proves", "TaskFlow AI is a flagship-level MVP for agent workflow automation rather than a chatbot or RAG clone. It demonstrates stateful runs, tool calls, approval gates, traceability, retries, cost controls, and AgentOps without claiming production completeness."],
  ["Architecture diagram", "Next.js App Router frontend calls FastAPI. FastAPI owns auth, RBAC, workflow APIs, LangGraph runtime, tool gateway, usage logs, and SSE run streams. SQLite is a quick-demo mode; PostgreSQL/Alembic production hardening is still planned."],
  ["LangGraph runtime flow", "The backend runtime uses LangGraph StateGraph nodes for workflow loading, permission validation, initialization, planning, tool routing, tool execution, approval pause/resume, condition routing, agent execution, review, finalize, and error handling."],
  ["Graph node list", "load_workflow -> validate_permissions -> initialize_run -> planner -> tool_router. Conditional edges route to execute_tool, approval_gate, agent_execute, reviewer, finalize, or error_handler. Tool, approval, and agent nodes return through condition_router until the run completes or fails."],
  ["State shape", "AgentRunState carries run_id, workspace_id, workflow_id, workflow_version, user_id, role, input, workflow_definition, current_step_id, status, plan, tool_results, approvals, messages, final_output, error, cost, limits, trace_id, resume_approved, and next_action."],
  ["Workflow builder", "The workflow detail page renders the definition as a React Flow graph and JSON definition view. Public guest mode is read-only except for running the prebuilt demo workflow."],
  ["Tool registry", "Tools have slugs, JSON schemas, enabled flags, approval requirements, timeouts, retries, and auditable tool_call records."],
  ["MCP-style gateway", "TaskFlow AI implements an MCP-style internal gateway to demonstrate tool discovery, schema validation, permission checks, and auditable tool invocation. It is not presented as a full external MCP server/client."],
  ["Human approval flow", "The approval_gate graph node creates pending approval records, changes run status to waiting_for_approval, and ends the graph in a paused state. The approve endpoint updates the same approval row and resumes the same run_id through the graph. Reject routes back through approval_gate to error_handler and marks the run failed."],
  ["Live execution trace", "Run pages consume an SSE endpoint that emits run, step, and approval updates. The page shows current status, timeline, tool calls, approval card, final output, cost, tokens, latency, and trace ID."],
  ["Retry/error recovery", "Tool invocation validates inputs, records failures, retries according to tool policy, and surfaces errors on the run record instead of hiding them. Runtime limits for max steps, max cost, and max tool calls route to error_handler, and failed runs avoid extra model/tool charges after the limit failure."],
  ["Cost and loop limits", "Workspace settings include max steps, max run credits, max tool calls, max runtime, and default model. Demo runs deduct credits and write credit transactions."],
  ["AgentOps dashboard", "The dashboard reports total runs, success/failure counts, waiting approvals, credits, tool calls, provider usage, and Langfuse enabled/disabled state."],
  ["Security and RBAC", "Workspace roles are owner, admin, operator, viewer, and guest. Guest can run and approve only the prebuilt demo workflow and cannot edit tools or settings."],
  ["Provider strategy", "ModelGateway supports demo-local now and is shaped for DeepSeek, Qwen, and OpenAI-compatible providers. Missing keys keep the app working with honest simulated model responses."],
  ["Langfuse observability", "Langfuse is configuration-ready but external trace sending is still a planned upgrade. Without keys, local structured timeline and trace IDs remain available."],
  ["Database schema summary", "The backend includes users, workspaces, workspace_members, workflows, workflow_versions, agent_runs, agent_run_steps, tools, tool_calls, approvals, usage_logs, credit_transactions, scheduled_triggers, and webhook_events."],
  ["Files to review", "services/api/app/runtime/engine.py contains the LangGraph nodes and conditional edges. services/api/app/runtime/state.py defines AgentRunState. services/api/app/services/tool_gateway.py performs schema-validated tool invocation and retry logging. services/api/app/api/routes.py wires run creation, approval resume/reject, replay, SSE, usage, and MCP-style routes. services/api/app/tests/test_langgraph_runtime.py verifies graph behavior."],
  ["Known limitations", "Public demo tools use seeded demo data. External write tools are simulated in public demo mode. SQLite is quick-demo mode. Celery/Redis worker, Alembic migrations, active scheduled triggers, editable workflow publishing, and real Langfuse trace sending are still planned hardening work."],
  ["Production deployment notes", "Use managed Postgres and Redis, rotate JWT/webhook secrets, enable provider and Langfuse keys server-side only, deploy frontend to Vercel and FastAPI to a hosted backend, and run CI before release."]
];

export default function TechnicalReviewPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <Link className="text-sm text-accent" href="/">Back home</Link>
      <h1 className="mt-4 text-4xl font-black text-ink">Technical Review</h1>
      <p className="mt-4 text-lg leading-8 text-slate-600">TaskFlow AI is a flagship-level MVP for designing, running, approving, monitoring, and auditing multi-step AI workflows. It is not yet labeled flagship complete.</p>
      <div className="mt-8 grid gap-4">
        {sections.map(([title, body]) => <section className="panel p-5" key={title}><h2 className="text-xl font-bold">{title}</h2><p className="mt-2 leading-7 text-slate-600">{body}</p></section>)}
      </div>
    </main>
  );
}
