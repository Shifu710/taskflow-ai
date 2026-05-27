"use client";

import "@xyflow/react/dist/style.css";
import { Background, Controls, ReactFlow } from "@xyflow/react";
import { Play, Rocket } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { api, Workflow } from "@/lib/api";

export default function WorkflowDetailPage() {
  const { workspaceId, workflowId } = useParams<{ workspaceId: string; workflowId: string }>();
  const router = useRouter();
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [versions, setVersions] = useState<Array<{ id: string; version: number; created_at: string }>>([]);
  const [query, setQuery] = useState("Research Bytebase and create a short outreach brief.");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    api<Workflow>(`/workspaces/${workspaceId}/workflows/${workflowId}`).then(setWorkflow);
    api<{ versions: Array<{ id: string; version: number; created_at: string }> }>(`/workspaces/${workspaceId}/workflows/${workflowId}/versions`).then((res) => setVersions(res.versions)).catch(() => setVersions([]));
  }, [workspaceId, workflowId]);
  const graph = useMemo(() => {
    const steps = workflow?.definition_json.steps ?? [];
    return {
      nodes: steps.map((step, index) => ({ id: step.id, position: { x: index * 190, y: index % 2 ? 115 : 20 }, data: { label: `${step.id}\n${step.type}` }, type: "default" })),
      edges: steps.slice(1).map((step, index) => ({ id: `${steps[index].id}-${step.id}`, source: steps[index].id, target: step.id }))
    };
  }, [workflow]);

  async function run() {
    setBusy(true);
    const res = await api<{ run_id: string }>(`/workspaces/${workspaceId}/workflows/${workflowId}/runs`, { method: "POST", body: JSON.stringify({ input: { query } }) });
    router.push(`/workspaces/${workspaceId}/runs/${res.run_id}`);
  }

  async function publish() {
    setNotice("");
    try {
      const res = await api<{ status: string; version: number }>(`/workspaces/${workspaceId}/workflows/${workflowId}/publish`, { method: "POST" });
      setWorkflow((current) => current ? { ...current, status: res.status, version: res.version } : current);
      setNotice(`Published version ${res.version}`);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "Could not publish workflow");
    }
  }

  if (!workflow) return <div className="panel p-5">Loading workflow...</div>;
  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">{workflow.name}</h1>
          <p className="mt-2 max-w-3xl text-slate-600">{workflow.description}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn-secondary" disabled={workflow.guest_read_only} onClick={publish}><Rocket size={18} /> Publish</button>
          <button className="btn-primary" disabled={busy || workflow.status === "template"} onClick={run}><Play size={18} /> Run</button>
        </div>
      </div>
      {notice ? <div className="mt-4 rounded-md border border-line bg-white p-3 text-sm text-slate-700">{notice}</div> : null}
      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_380px]">
        <div className="panel h-[460px] overflow-hidden p-2">
          <ReactFlow nodes={graph.nodes} edges={graph.edges} fitView>
            <Background />
            <Controls />
          </ReactFlow>
        </div>
        <div className="grid gap-4">
          <div className="panel p-5">
            <h2 className="font-bold">Run input</h2>
            <textarea className="mt-3 min-h-28 w-full rounded-md border border-line p-3 text-sm" value={query} onChange={(e) => setQuery(e.target.value)} />
            <p className="mt-3 text-sm text-slate-500">Guest can run the prebuilt demo workflow and approve its demo-only approval gate.</p>
          </div>
          <div className="panel p-5">
            <h2 className="font-bold">Node config</h2>
            <div className="mt-3 grid gap-2 text-sm">
              {(workflow.definition_json.steps ?? []).map((step) => (
                <div className="rounded-md border border-line p-3" key={step.id}>
                  <div className="font-semibold">{step.id}</div>
                  <div className="text-slate-500">type: {step.type}{step.tool ? ` / tool: ${step.tool}` : ""}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="panel p-5">
            <h2 className="font-bold">Version history</h2>
            <div className="mt-3 grid gap-2 text-sm text-slate-600">
              {versions.length ? versions.map((version) => (
                <div className="rounded-md bg-slate-50 px-3 py-2" key={version.id}>v{version.version} - {new Date(version.created_at).toLocaleString()}</div>
              )) : <p>No versions loaded.</p>}
            </div>
          </div>
          <div className="panel p-5">
            <h2 className="font-bold">Definition JSON</h2>
            <pre className="mt-3 max-h-56 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(workflow.definition_json, null, 2)}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}
