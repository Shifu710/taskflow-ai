"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { StatusPill } from "@/components/AppShell";
import { api } from "@/lib/api";

type Run = { id: string; status: string; workflow_id: string; credits_used: number; tool_calls_count: number; created_at: string };

export default function RunsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [rows, setRows] = useState<Run[]>([]);
  useEffect(() => { api<{ runs: Run[] }>(`/workspaces/${workspaceId}/runs`).then((res) => setRows(res.runs)); }, [workspaceId]);
  return (
    <div>
      <h1 className="text-3xl font-bold">Runs</h1>
      <div className="mt-6 grid gap-3">
        {rows.map((run) => (
          <Link href={`/workspaces/${workspaceId}/runs/${run.id}`} key={run.id} className="panel flex flex-wrap items-center justify-between gap-3 p-4 hover:border-teal-300">
            <div><div className="font-semibold">{run.id}</div><div className="text-sm text-slate-500">{run.workflow_id}</div></div>
            <StatusPill status={run.status} />
            <div className="text-sm text-slate-500">{run.credits_used} credits / {run.tool_calls_count} tools</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
