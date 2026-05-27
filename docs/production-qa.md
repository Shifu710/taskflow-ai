# Production QA Checklist

- Date: 2026-05-27
- Frontend URL: https://taskflow-ai-seven-eosin.vercel.app
- Interim API URL (dev tunnel): https://masters-terrorism-departments-vacuum.trycloudflare.com
- Permanent API URL (Render blueprint): pending — apply `render.yaml` on Render
- Commit SHA tested: `af4b190` (live QA on public frontend + interim API)
- Database provider (interim QA): SQLite on the API host (not production Postgres yet)
- Database provider (target production): Render managed PostgreSQL (`taskflow-db` in `render.yaml`)

## Routes Tested (production frontend)

- `/`
- `/login`
- `/register`
- `/demo`
- `/technical-review`
- `/workspaces`
- `/workspaces/ws_demo/dashboard`
- `/workspaces/ws_demo/workflows`
- `/workspaces/ws_demo/workflows/wf_competitor`
- `/workspaces/ws_demo/runs`
- `/workspaces/ws_demo/runs/7a1dec99-1f71-40c6-8e5a-5cef9deaa6f4`
- `/workspaces/ws_demo/tools`
- `/workspaces/ws_demo/approvals`
- `/workspaces/ws_demo/usage`
- `/workspaces/ws_demo/settings`
- `GET /health` on interim API host

## Acceptance Checks (live)

- Guest demo result: **passed** on production frontend.
- Workflow run tested: **passed** with `Competitor Research & Outreach Agent`.
- Planner step starts: **passed** (`plan` step persisted).
- Tool calls execute: **passed** (`demo_search`, `company_profile_lookup`).
- Approval tested: **passed** (`waiting_for_approval`).
- Approval resume tested: **passed** (same `run_id` resumed after approve).
- Reviewer/finalize tested: **passed** (structured final report rendered).
- Credits before/after: **passed** (`credits_used: 3.5` on completed run).
- Usage log observed: **passed** (`model_call`, `tool_call` on usage page).
- Run replay tested: **passed** via API (`POST .../replay` created new run).
- Technical Review page tested: **passed**.
- Broken links: **none** found in visible app navigation during live pass.

## Checks Run

```txt
npm install
npm run typecheck --workspace apps/web
npm run lint --workspace apps/web
npm run build --workspace apps/web
python -m ruff check services/api/app --select F
python -m pytest services/api/app/tests
cd services/api && python -m alembic -c alembic.ini upgrade head
```

Python commands used Codex runtime `python.exe` 3.12.13 where system `python` was unavailable.

## Known Issues

- **Permanent hosted backend is not live yet.** Render blueprint (`render.yaml`) is ready but requires a one-time Render dashboard apply (GitHub sign-in).
- Vercel currently points at an **interim Cloudflare tunnel** for API access during QA. Replace `NEXT_PUBLIC_API_BASE_URL` with `https://<render-service>/api/v1` after Render deploy.
- Interim QA used SQLite, not managed PostgreSQL. Production must use Render Postgres + Alembic migrate on container start.
- Public demo uses seeded demo data, not live web search.
- External write tools are simulated in public demo mode.
- `TASKFLOW_USE_CELERY=false` for first public demo; Redis/Celery path exists for Docker but is not verified in production.
- Langfuse trace sending is not implemented; local trace IDs and structured run logs are available.
- Scheduled triggers are schema/API-level only; no active production scheduler verified.
