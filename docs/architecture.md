# TaskFlow AI Architecture

TaskFlow AI is an enterprise AI Agent workflow automation platform. The frontend is a Next.js App Router app. The backend is FastAPI with SQLAlchemy models for workspaces, RBAC, workflows, tools, runs, approvals, usage, credits, triggers, and webhook events.

```mermaid
flowchart LR
  Web[Next.js App Router] --> API[FastAPI /api/v1]
  API --> Auth[JWT + RBAC]
  API --> Runtime[LangGraph Runtime]
  Runtime --> Gateway[MCP-style Tool Gateway]
  Gateway --> Tools[Demo-safe Tool Registry]
  Runtime --> DB[(PostgreSQL or SQLite local)]
  API --> SSE[SSE Run Stream]
  API --> Usage[Usage and Credit Logs]
  API --> Langfuse[Langfuse-ready optional tracing]
```

The public demo target is `demo-local` model responses with seeded business data. Runtime state, approvals, tool calls, usage logs, and credit transactions persist through SQLAlchemy. SQLite is the quick-demo path; PostgreSQL with Alembic is the intended production data path.

Deployment status: local verification is passing, but the public frontend plus hosted FastAPI backend plus managed PostgreSQL demo has not been verified yet.
