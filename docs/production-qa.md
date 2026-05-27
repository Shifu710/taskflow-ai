# Production QA Checklist

- Date: 2026-05-27
- Deployment URL: Not deployed yet
- Local QA URL: `http://127.0.0.1:3000`
- API URL: `http://127.0.0.1:8000`
- Commit SHA tested locally: `5fb8f30`

## Routes Tested Locally

- `/`
- `/login`
- `/register`
- `/demo`
- `/technical-review`
- `/workspaces`
- `/workspaces/ws_demo/dashboard`
- `/workspaces/ws_demo/workflows`
- `/workspaces/ws_demo/workflows/new`
- `/workspaces/ws_demo/workflows/wf_competitor`
- `/workspaces/ws_demo/runs`
- `/workspaces/ws_demo/runs/{runId}`
- `/workspaces/ws_demo/tools`
- `/workspaces/ws_demo/approvals`
- `/workspaces/ws_demo/usage`
- `/workspaces/ws_demo/settings`
- `/health`

## Acceptance Checks

- Guest demo result: passed locally.
- Workflow run tested: passed with `Competitor Research & Outreach Agent`.
- Planner step starts: passed, persisted as `plan`.
- Tool calls execute: passed, `demo_search` and `company_profile_lookup` logged tool calls.
- Approval tested: passed, run paused at `waiting_for_approval`.
- Approval resume tested: passed, approving resumed the same `run_id`.
- Reviewer/finalize tested: passed, final structured report appeared.
- Credits before/after: passed, run page shows `Credits used` and API tests verify deduction.
- Usage log observed: passed, usage page shows `model_call` and `tool_call`.
- Run replay tested: passed, replay creates a new run from the original input.
- Technical Review page tested: passed, includes LangGraph runtime flow, MCP-style gateway, PostgreSQL/Alembic data path, provider strategy, and known limitations.
- Broken links: no broken visible app navigation found in local route pass.

## Checks Run

```txt
npm.cmd run typecheck --workspace apps/web
npm.cmd run lint --workspace apps/web
npm.cmd run build --workspace apps/web
C:\Users\Gamal\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check services/api/app --select F
C:\Users\Gamal\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest services/api/app/tests
cd services/api && C:\Users\Gamal\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m alembic -c alembic.ini upgrade head
```

## Known Issues

- Production deployment is still pending.
- Public demo uses seeded demo data, not live web search.
- External write tools are simulated in public demo mode.
- Celery/Redis worker mode is wired for Docker, while local quick-demo mode defaults to synchronous execution.
- Langfuse trace sending is not implemented yet; local trace IDs and structured run logs are available.
- Scheduled trigger schema exists, but active background schedule execution is not production-hardened yet.
