# TaskFlow AI Current State Audit

Date: 2026-05-27

Source of truth: `C:/Users/Gamal/Downloads/taskflow-ai-master-build-prompt-for-codex.md`

## Current Files

Top-level structure currently present:

```txt
.github/workflows/ci.yml
apps/api
apps/web
docs/architecture.md
docs/demo-script.md
docs/production-qa.md
docker-compose.yml
.env.example
package.json
README.md
```

Important note: the current backend lives in `apps/api`, but the master prompt requires `services/api`. This should be fixed early so the repository matches the requested flagship structure.

## Current Frontend Stack

Current frontend implementation:

- Next.js App Router in `apps/web`
- TypeScript
- Tailwind CSS
- React Flow via `@xyflow/react`
- Recharts
- Zod
- Lucide icons
- Client-side API helper in `apps/web/lib/api.ts`

Missing or incomplete compared with the master prompt:

- TanStack Query is not installed or used.
- React Hook Form is not installed or used.
- shadcn/ui package scaffolding is not present, though the UI has local reusable styling.
- Workflow builder editing is still thin. The current detail page visualizes workflow data, but the full save draft, publish, node config, version history, and validation workflow needs hardening.

## Current Backend Stack

Current backend implementation:

- FastAPI in `apps/api`
- Pydantic
- SQLAlchemy 2.x models
- SQLite quick-demo default through `DATABASE_URL`
- PostgreSQL Docker Compose path through `postgresql+psycopg`
- JSON schema validation for tools
- JWT-style auth utilities
- LangGraph dependency present and used by `apps/api/app/runtime/engine.py`

Missing or incomplete compared with the master prompt:

- Alembic is not implemented.
- Backend directory is not yet `services/api`.
- Redis exists in Docker Compose but is not deeply used.
- Celery is not installed or wired.
- Ruff/backend lint command is not configured.
- Active scheduled trigger execution is not implemented.

## Whether App Runs

Frontend checks from this audit:

- `npm.cmd run typecheck --workspace apps/web` passed.
- `npm.cmd run lint --workspace apps/web` passed.
- `npm.cmd run build --workspace apps/web` passed.
- Next.js build generated all required visible routes, including `/workspaces/[workspaceId]/runs/[runId]` and `/technical-review`.

Backend checks from this audit:

- `pytest apps/api/app/tests` could not run because `pytest` is not installed on the shell path.
- `python -m pytest apps/api/app/tests` could not run because `python` is not available on the shell path.
- `py -m pytest apps/api/app/tests` could not run because `py` is not available on the shell path.

This does not prove backend tests are broken. It means the current Windows shell does not expose a Python executable. Backend tests must be rerun through Docker, a local Python install, or a bundled Python runtime in the next phase.

## Whether Auth Exists

Auth exists in the backend:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/guest`
- JWT creation and current-user dependency
- Seeded users:
  - `guest@taskflow.ai / guest123`
  - `demo@taskflow.ai / demo12345`

Missing or incomplete:

- Register route is not implemented in the API, although `/register` exists in the frontend.
- Logout is handled client-side at most, not as a backend session invalidation flow.
- Session/JWT behavior is demo-grade and should be documented as such.

## Whether Workspace Exists

Workspace support exists:

- `Workspace` and `WorkspaceMember` models
- `TaskFlow Demo Workspace` seeded as `ws_demo`
- Workspace list API
- Workspace dashboard route and page
- RBAC roles are represented through `WorkspaceMember.role`

Missing or incomplete:

- Workspace member management page/API is not implemented.
- Full RBAC coverage needs to be verified after the structure refactor.

## Whether Workflow Pages Exist

Frontend routes currently exist:

- `/`
- `/login`
- `/register`
- `/demo`
- `/technical-review`
- `/workspaces`
- `/workspaces/[workspaceId]/dashboard`
- `/workspaces/[workspaceId]/workflows`
- `/workspaces/[workspaceId]/workflows/new`
- `/workspaces/[workspaceId]/workflows/[workflowId]`
- `/workspaces/[workspaceId]/runs`
- `/workspaces/[workspaceId]/runs/[runId]`
- `/workspaces/[workspaceId]/tools`
- `/workspaces/[workspaceId]/approvals`
- `/workspaces/[workspaceId]/usage`
- `/workspaces/[workspaceId]/settings`

Backend workflow endpoints currently exist for listing, detail, run creation, webhook trigger, run list, run detail, replay, approvals, tools, MCP-style tool manifest, MCP-style invocation, and usage.

Missing or incomplete:

- `POST /workflows` create draft API is missing.
- Save draft / publish / archive APIs are missing.
- Version history API is not complete.
- The master prompt says to start with only two templates. Current seed data includes more than two template workflows.

## Whether Backend Exists

Yes. Backend exists and includes:

- FastAPI app startup
- Database models
- Seed data
- Auth routes
- Workspace routes
- Workflow routes
- Run routes
- Approval routes
- Tool registry routes
- MCP-style gateway routes
- Usage routes
- Webhook route
- Tests under `apps/api/app/tests`

Main gap: location should be migrated from `apps/api` to `services/api`.

## Whether LangGraph Exists

Yes. LangGraph is imported and `StateGraph` is compiled in `apps/api/app/runtime/engine.py`.

Current graph nodes:

- `load_workflow`
- `validate_permissions`
- `initialize_run`
- `planner`
- `tool_router`
- `execute_tool`
- `approval_gate`
- `condition_router`
- `agent_execute`
- `reviewer`
- `finalize`
- `error_handler`

The nodes are meaningful, persist steps, mutate state, route conditionally, call tools, pause on approval, resume after approval, and finalize or fail runs.

Remaining concerns:

- Execution is synchronous; Celery/Redis are not yet the production execution path.
- State is reconstructed from the database on resume rather than using LangGraph checkpoint storage.
- Timeout handling is mostly represented by limits fields, not active cancellation.

## Whether Tool Calling Exists

Yes. Tool calling exists through:

- `Tool` model
- `ToolCall` model
- Tool seed data
- `app/services/tool_gateway.py`
- `app/tools/demo_tools.py`
- JSON schema validation with `jsonschema`
- Tool call logs and usage logs

Current seed tools include required tools plus extra tools:

- Required present: `demo_search`, `company_profile_lookup`, `calculator`, `email_draft_generator`, `webhook_sender_demo`, `task_creator_demo`
- Required missing by exact slug: `create_ticket_demo`
- Extra present: `csv_analyzer`, `document_lookup_demo`, `http_request_demo`, `crm_note_writer_demo`

The master prompt requires starting with the exact seeded tools and two templates, so the seed data needs cleanup.

## Whether Approval Flow Exists

Yes. Approval flow exists:

- `Approval` model
- approval list page
- approve/reject endpoints
- LangGraph `approval_gate` creates a pending approval
- run status becomes `waiting_for_approval`
- approval resumes the same `run_id`
- rejection routes to `error_handler`

Missing or incomplete:

- Expiration/cancelled handling is modeled but not active.
- Approval usage logs should be strengthened.

## Whether Live Execution Trace Exists

Yes, a minimum SSE trace exists:

- `GET /api/v1/workspaces/{workspace_id}/runs/{run_id}/events/stream`
- Run detail page can display run, steps, tool calls, approvals, status, final output, credits, tokens, and trace ID.

Missing or incomplete:

- Current SSE event name is mostly `run_update`, not the full event taxonomy required by the prompt (`run_started`, `step_started`, `tool_call_started`, etc.).
- Graph progress is present through persisted steps, but event typing should be upgraded.

## Whether Deployment Exists

Deployment assets exist:

- `docker-compose.yml`
- frontend Dockerfile
- backend Dockerfile
- GitHub Actions CI
- public GitHub repo exists

Missing or incomplete:

- TaskFlow AI is not yet visible as a Vercel project.
- Production deployment URL is not set.
- Backend hosting is not completed.
- Production QA doc exists but must be regenerated after a real live deployment.

## What Is Missing

Highest priority gaps against the master prompt:

1. Repository structure mismatch: backend must move from `apps/api` to `services/api`.
2. Register API and complete auth/session behavior.
3. Workflow create/save/publish/version endpoints.
4. Seed data must be limited to the two required templates.
5. Tool seed list must match the required registry, including `create_ticket_demo`.
6. Alembic migrations and production PostgreSQL-first path.
7. Celery + Redis worker execution path.
8. TanStack Query, React Hook Form, and shadcn/ui alignment.
9. More explicit SSE event taxonomy.
10. ModelGateway currently has demo-local and placeholder provider behavior; DeepSeek/Qwen/OpenAI-compatible calls need real server-side implementation.
11. Langfuse external trace sending is not implemented.
12. Scheduled trigger execution is not active.
13. GitHub Actions needs backend lint/ruff.
14. TaskFlow AI itself is not deployed as a live project.

## Recommended Next Step

Continue with Phase 1 and Phase 2 in a narrow, testable order:

1. Migrate backend from `apps/api` to `services/api` and update scripts, Docker, CI, docs, and imports.
2. Add missing backend commands and make Python test execution reproducible, preferably through Docker if local Python is unavailable.
3. Add the missing register route and tighten auth/workspace/RBAC behavior.
4. Clean seed workflows and tools to match the required two-template, seven-tool scope.
5. Add workflow draft/create/publish/version endpoints before polishing the builder UI.

Do not call the project complete until the live demo flow in the master prompt works end to end on a deployed URL.
