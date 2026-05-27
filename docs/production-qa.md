# Production QA Checklist

- Date: 2026-05-27
- Frontend URL: https://taskflow-ai-seven-eosin.vercel.app
- Permanent API URL: https://taskflow-ai-api.onrender.com/api/v1
- Vercel deployment ID: `dpl_9Ky8tenpyZCWwFvCfisTEKsbT3dY`
- Latest commit SHA tested: `48980f4`
- Backend provider: Render (`taskflow-ai-api`, service `srv-d8bndnkp3tds73alfmm0`)
- Database provider: Render managed PostgreSQL (`taskflow-db`, `dpg-d8bnmqkp3tds73alm1e0-a`, PostgreSQL 16)
- Migration result: **passed** (`alembic -c alembic.ini upgrade head` in Render start command)
- Seed verification result: **passed** (2 workflows, 7 demo tools on `ws_demo`)

## Historical note

An interim Cloudflare tunnel was used for earlier QA while Render was failing startup seeds. Final QA was rerun against **Render + managed PostgreSQL + Vercel** with `NEXT_PUBLIC_API_BASE_URL` pointing at the Render API.

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
- `/workspaces/ws_demo/runs` and live run detail pages
- `/workspaces/ws_demo/tools`
- `/workspaces/ws_demo/approvals`
- `/workspaces/ws_demo/usage`
- `/workspaces/ws_demo/settings`
- `GET https://taskflow-ai-api.onrender.com/health`

## Acceptance Checks (live)

- Guest demo result: **passed** (auto guest login from `/demo`).
- Workflow run tested: **passed** with `Competitor Research & Outreach Agent`.
- Planner step starts: **passed**.
- Tool calls execute: **passed** (`demo_search`, `company_profile_lookup`).
- Approval tested: **passed** (`waiting_for_approval`).
- Approval resume tested: **passed** (same run resumed after approve).
- Reviewer/finalize tested: **passed** (structured final report rendered).
- Credits before/after: **passed** (workspace balance decreased after runs; completed run recorded `credits_used`).
- Usage log observed: **passed** (`model_call` and `tool_call` rows on usage page).
- Run replay tested: **passed** (UI replay opened a new run ID).
- Technical Review page tested: **passed**.
- Broken links: **none** found in visible app navigation during live pass.
- Production bundle/network: **passed** — deployed JS calls `taskflow-ai-api.onrender.com`; no Cloudflare tunnel or `localhost:8000` API calls observed.

## Backend API Verification

```txt
GET  /health -> 200 {"ok": true}
POST /api/v1/auth/guest -> token + workspace_id ws_demo
GET  /api/v1/workspaces/ws_demo/workflows -> Competitor + Support triage workflows
GET  /api/v1/workspaces/ws_demo/tools -> 7 seeded demo tools
```

## Checks Run (repo)

```txt
npm run typecheck --workspace apps/web
npm run lint --workspace apps/web
npm run build --workspace apps/web
python -m ruff check services/api/app --select F
python -m pytest services/api/app/tests
```

Python commands used Codex runtime Python 3.12.13 where system `python` was unavailable.

## Known Limitations

- Public demo uses `demo-local` AI responses, not live DeepSeek/Qwen inference.
- Demo tools use seeded data, not live web search.
- External write tools are simulated in public demo mode.
- `TASKFLOW_USE_CELERY=false` on Render; Redis/Celery is not enabled for the first public demo.
- Langfuse trace sending is not implemented.
- Scheduled triggers are schema/API-level only; no active production scheduler.
- Render free-tier Postgres expires after the free trial window unless upgraded.
