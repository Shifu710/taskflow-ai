"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function WorkspacesPage() {
  const [rows, setRows] = useState<Array<{ id: string; name: string; role: string; credits_balance: number }>>([]);
  useEffect(() => { api<{ workspaces: typeof rows }>("/workspaces").then((res) => setRows(res.workspaces)).catch(() => setRows([])); }, []);
  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="text-3xl font-bold">Workspaces</h1>
      <div className="mt-6 grid gap-4">
        {rows.map((workspace) => (
          <Link key={workspace.id} href={`/workspaces/${workspace.id}/dashboard`} className="panel block p-5 hover:border-teal-300">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold">{workspace.name}</h2>
                <p className="mt-1 text-sm text-slate-500">Role: {workspace.role}</p>
              </div>
              <div className="text-right text-sm text-slate-500">Credits<br /><span className="text-xl font-bold text-ink">{workspace.credits_balance}</span></div>
            </div>
          </Link>
        ))}
      </div>
    </main>
  );
}
