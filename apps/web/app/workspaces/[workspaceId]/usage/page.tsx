"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Usage = { id: string; run_id: string | null; event_type: string; provider: string; model: string; tool_slug: string | null; credits_used: number; latency_ms: number };

export default function UsagePage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [rows, setRows] = useState<Usage[]>([]);
  useEffect(() => { api<{ usage_logs: Usage[] }>(`/workspaces/${workspaceId}/usage`).then((res) => setRows(res.usage_logs)); }, [workspaceId]);
  return (
    <div>
      <h1 className="text-3xl font-bold">Usage Logs</h1>
      <p className="mt-2 text-slate-600">Model calls, tool calls, credits, latency, and provider metadata are recorded for auditability.</p>
      <div className="panel mt-6 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-500"><tr><th className="p-3">Type</th><th>Provider</th><th>Model/Tool</th><th>Credits</th><th>Latency</th><th>Run</th></tr></thead>
          <tbody>{rows.map((row) => <tr className="border-t border-line" key={row.id}><td className="p-3">{row.event_type}</td><td>{row.provider}</td><td>{row.tool_slug ?? row.model}</td><td>{row.credits_used}</td><td>{row.latency_ms}ms</td><td className="max-w-56 truncate">{row.run_id}</td></tr>)}</tbody>
        </table>
      </div>
    </div>
  );
}
