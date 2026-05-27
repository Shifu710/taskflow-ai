"use client";

import { Save } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

const defaultDefinition = {
  name: "Draft Agent Workflow",
  trigger: { type: "manual" },
  steps: [
    { id: "plan", type: "planner", max_retries: 0 },
    { id: "research", type: "tool_call", tool: "demo_search", max_retries: 1 },
    { id: "approval", type: "approval", message: "Approve continuing this workflow?" },
    { id: "draft", type: "agent", agent: "draft_writer" },
    { id: "review", type: "reviewer" },
    { id: "final", type: "formatter" }
  ]
};

export default function NewWorkflowPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const router = useRouter();
  const [name, setName] = useState("Draft Agent Workflow");
  const [description, setDescription] = useState("A draft workflow with planner, tool call, approval, agent, reviewer, and formatter nodes.");
  const [definition, setDefinition] = useState(JSON.stringify(defaultDefinition, null, 2));
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const parsed = JSON.parse(definition);
      const created = await api<{ id: string }>(`/workspaces/${workspaceId}/workflows`, {
        method: "POST",
        body: JSON.stringify({ name, description, definition_json: parsed, status: "draft" })
      });
      router.push(`/workspaces/${workspaceId}/workflows/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save workflow");
      setBusy(false);
    }
  }

  return (
    <div>
      <h1 className="text-3xl font-bold">New Workflow</h1>
      <form className="mt-6 grid gap-4 lg:grid-cols-[1fr_420px]" onSubmit={submit}>
        <div className="panel p-5">
          <label className="text-sm font-semibold">Name</label>
          <input className="mt-2 w-full rounded-md border border-line px-3 py-2" value={name} onChange={(event) => setName(event.target.value)} required />
          <label className="mt-4 block text-sm font-semibold">Description</label>
          <textarea className="mt-2 min-h-24 w-full rounded-md border border-line px-3 py-2" value={description} onChange={(event) => setDescription(event.target.value)} />
          <label className="mt-4 block text-sm font-semibold">Definition JSON</label>
          <textarea className="mt-2 min-h-[420px] w-full rounded-md border border-line bg-slate-950 p-3 font-mono text-sm text-slate-100" value={definition} onChange={(event) => setDefinition(event.target.value)} />
        </div>
        <aside className="panel h-fit p-5">
          <h2 className="font-bold">Draft controls</h2>
          <p className="mt-2 text-sm text-slate-600">Owners, admins, and operators can save drafts. Guest users are rejected by backend RBAC.</p>
          <div className="mt-4 grid gap-2 text-sm">
            {["trigger", "planner", "tool_call", "approval", "condition", "agent", "reviewer", "formatter", "webhook", "delay", "end"].map((item) => (
              <span className="rounded-md bg-slate-50 px-3 py-2" key={item}>{item}</span>
            ))}
          </div>
          {error ? <p className="mt-4 rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
          <button className="btn-primary mt-5 w-full justify-center" disabled={busy}><Save size={18} /> {busy ? "Saving..." : "Save draft"}</button>
        </aside>
      </form>
    </div>
  );
}
