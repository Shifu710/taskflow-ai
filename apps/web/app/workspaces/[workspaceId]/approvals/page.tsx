"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { StatusPill } from "@/components/AppShell";
import { api } from "@/lib/api";

type Approval = { id: string; run_id: string; step_id: string; status: string; message: string; payload_json: unknown };

export default function ApprovalsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [rows, setRows] = useState<Approval[]>([]);
  useEffect(() => { api<{ approvals: Approval[] }>(`/workspaces/${workspaceId}/approvals`).then((res) => setRows(res.approvals)); }, [workspaceId]);
  async function decide(id: string, action: "approve" | "reject") {
    await api(`/workspaces/${workspaceId}/approvals/${id}/${action}`, { method: "POST", body: JSON.stringify({ decision_note: `${action} from approvals queue` }) });
    const res = await api<{ approvals: Approval[] }>(`/workspaces/${workspaceId}/approvals`);
    setRows(res.approvals);
  }
  return (
    <div>
      <h1 className="text-3xl font-bold">Approvals</h1>
      <div className="mt-6 grid gap-4">
        {rows.map((approval) => (
          <div className="panel p-5" key={approval.id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div><h2 className="font-bold">{approval.message}</h2><Link className="text-sm text-accent" href={`/workspaces/${workspaceId}/runs/${approval.run_id}`}>Open run {approval.run_id}</Link></div>
              <StatusPill status={approval.status} />
            </div>
            <pre className="mt-3 rounded-md bg-slate-50 p-3 text-xs">{JSON.stringify(approval.payload_json, null, 2)}</pre>
            {approval.status === "pending" ? <div className="mt-4 flex gap-3"><button className="btn-primary" onClick={() => decide(approval.id, "approve")}>Approve</button><button className="btn-secondary" onClick={() => decide(approval.id, "reject")}>Reject</button></div> : null}
          </div>
        ))}
      </div>
    </div>
  );
}
