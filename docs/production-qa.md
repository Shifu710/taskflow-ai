# Production QA Checklist

- Date: 2026-05-26
- Deployment URL: TBD
- Commit SHA: TBD

## Routes Tested

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
- `/workspaces/ws_demo/tools`
- `/workspaces/ws_demo/approvals`
- `/workspaces/ws_demo/usage`
- `/workspaces/ws_demo/settings`
- `/admin`

## Acceptance Checks

- Guest demo result: passed locally on `http://127.0.0.1:3000`
- Workflow run tested: passed, `Competitor Research & Outreach Agent`
- Approval tested: passed, run paused at `waiting_for_approval` and resumed after approval
- Credits before/after: passed through API tests and visible run metrics
- Usage log observed: passed, `/workspaces/ws_demo/usage`
- Run replay tested: passed through backend test
- Technical Review page tested: passed locally
- Known issues: public demo uses seeded data and simulated external writes; npm audit reports a moderate advisory through Next's bundled PostCSS dependency and suggests only a breaking downgrade, so it is documented rather than applied
