"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { StatusPill } from "@/components/AppShell";
import { api, Workflow } from "@/lib/api";

export default function WorkflowsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [rows, setRows] = useState<Workflow[]>([]);
  useEffect(() => { api<{ workflows: Workflow[] }>(`/workspaces/${workspaceId}/workflows`).then((res) => setRows(res.workflows)); }, [workspaceId]);
  return (
    <div>
      <div className="flex items-center justify-between">
        <div><h1 className="text-3xl font-bold">Workflows</h1><p className="mt-2 text-slate-600">Templates and published workflows. Guest mode is read-only except demo runs.</p></div>
        <Link className="btn-secondary" href={`/workspaces/${workspaceId}/workflows/new`}>New workflow</Link>
      </div>
      <div className="mt-6 grid gap-4">
        {rows.map((workflow) => (
          <Link key={workflow.id} href={`/workspaces/${workspaceId}/workflows/${workflow.id}`} className="panel block p-5 hover:border-teal-300">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div><h2 className="text-xl font-bold">{workflow.name}</h2><p className="mt-1 text-sm text-slate-600">{workflow.description}</p></div>
              <StatusPill status={workflow.status} />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
