"use client";

import { CheckCircle2, RotateCcw, XCircle } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@/components/AppShell";
import { api, API_BASE, getToken, RunDetail } from "@/lib/api";

export default function RunDetailPage() {
  const { workspaceId, runId } = useParams<{ workspaceId: string; runId: string }>();
  const router = useRouter();
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const pendingApproval = useMemo(() => detail?.approvals.find((item) => item.status === "pending"), [detail]);

  useEffect(() => {
    api<RunDetail>(`/workspaces/${workspaceId}/runs/${runId}`).then(setDetail);
    const source = new EventSource(`${API_BASE}/workspaces/${workspaceId}/runs/${runId}/events/stream?token=${getToken()}`);
    source.addEventListener("run_update", (event) => setDetail(JSON.parse((event as MessageEvent).data)));
    source.onerror = () => source.close();
    return () => source.close();
  }, [workspaceId, runId]);

  async function approve() {
    if (!pendingApproval) return;
    const res = await api<{ run: RunDetail["run"] }>(`/workspaces/${workspaceId}/approvals/${pendingApproval.id}/approve`, { method: "POST", body: JSON.stringify({ decision_note: "Approved in guest demo." }) });
    setDetail((old) => old ? { ...old, run: res.run } : old);
    api<RunDetail>(`/workspaces/${workspaceId}/runs/${runId}`).then(setDetail);
  }

  async function reject() {
    if (!pendingApproval) return;
    await api(`/workspaces/${workspaceId}/approvals/${pendingApproval.id}/reject`, { method: "POST", body: JSON.stringify({ decision_note: "Rejected in demo." }) });
    api<RunDetail>(`/workspaces/${workspaceId}/runs/${runId}`).then(setDetail);
  }

  async function replay() {
    const res = await api<{ run_id: string }>(`/workspaces/${workspaceId}/runs/${runId}/replay`, { method: "POST", body: "{}" });
    router.push(`/workspaces/${workspaceId}/runs/${res.run_id}`);
  }

  if (!detail) return <div className="panel p-5">Loading live run...</div>;
  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Live Run Trace</h1>
          <p className="mt-2 text-slate-600">{detail.run.id}</p>
        </div>
        <div className="flex gap-2"><StatusPill status={detail.run.status} /><button className="btn-secondary" onClick={replay}><RotateCcw size={16} /> Replay</button></div>
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_380px]">
        <div className="grid gap-3">
          {(detail.steps ?? []).map((step) => (
            <div key={step.id} className="panel p-4">
              <div className="flex items-center justify-between gap-3">
                <div><div className="font-bold">{step.step_id}</div><div className="text-sm text-slate-500">{step.step_type} / retries: {step.retry_count} / {step.latency_ms}ms</div></div>
                <StatusPill status={step.status} />
              </div>
              {step.output_json ? <pre className="mt-3 max-h-44 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(step.output_json, null, 2)}</pre> : null}
            </div>
          ))}
          {pendingApproval ? (
            <div className="panel border-amber-300 bg-amber-50 p-5">
              <h2 className="font-bold text-amber-900">Approval required</h2>
              <p className="mt-2 text-sm text-amber-800">{pendingApproval.message}</p>
              <pre className="mt-3 rounded-md bg-white p-3 text-xs">{JSON.stringify(pendingApproval.payload_json, null, 2)}</pre>
              <div className="mt-4 flex gap-3">
                <button className="btn-primary" onClick={approve}><CheckCircle2 size={16} /> Approve</button>
                <button className="btn-secondary" onClick={reject}><XCircle size={16} /> Reject</button>
              </div>
            </div>
          ) : null}
        </div>
        <div className="grid gap-4">
          <div className="panel p-5">
            <h2 className="font-bold">Run metrics</h2>
            <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
              <dt className="text-slate-500">Credits</dt><dd>{detail.run.credits_used}</dd>
              <dt className="text-slate-500">Tool calls</dt><dd>{detail.run.tool_calls_count}</dd>
              <dt className="text-slate-500">Tokens</dt><dd>{detail.run.prompt_tokens + detail.run.completion_tokens}</dd>
              <dt className="text-slate-500">Trace ID</dt><dd className="break-all">{detail.run.trace_id}</dd>
            </dl>
          </div>
          <div className="panel p-5">
            <h2 className="font-bold">Tool calls</h2>
            <div className="mt-3 grid gap-3">
              {(detail.tool_calls ?? []).map((call) => <div key={call.id} className="rounded-md border border-line p-3 text-sm"><div className="font-semibold">{call.tool_name}</div><div className="text-slate-500">{call.status}, retry {call.retry_count}, {call.latency_ms}ms</div></div>)}
            </div>
          </div>
          {detail.run.final_output_json ? (
            <div className="panel p-5">
              <h2 className="font-bold">Final structured report</h2>
              <pre className="mt-3 max-h-96 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(detail.run.final_output_json, null, 2)}</pre>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
