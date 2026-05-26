"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { Stat } from "@/components/AppShell";
import { api, DEMO_WORKFLOW_ID } from "@/lib/api";

export default function DashboardPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [data, setData] = useState<Record<string, number | boolean>>({});
  useEffect(() => { api<Record<string, number | boolean>>(`/workspaces/${workspaceId}/dashboard`).then(setData); }, [workspaceId]);
  const chart = [
    { day: "Mon", runs: 3, credits: 12 },
    { day: "Tue", runs: Number(data.total_runs ?? 0), credits: Number(data.credits_used ?? 0) }
  ];
  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-ink">AgentOps Dashboard</h1>
          <p className="mt-2 text-slate-600">Operational view for runs, approvals, credits, tools, and provider usage.</p>
        </div>
        <Link className="btn-primary" href={`/workspaces/${workspaceId}/workflows/${DEMO_WORKFLOW_ID}`}>Open Demo Workflow</Link>
      </div>
      <div className="mt-6 grid gap-4 md:grid-cols-4">
        <Stat label="Total runs" value={Number(data.total_runs ?? 0)} />
        <Stat label="Successful runs" value={Number(data.successful_runs ?? 0)} />
        <Stat label="Waiting approvals" value={Number(data.waiting_approvals ?? 0)} />
        <Stat label="Credits used" value={Number(data.credits_used ?? 0)} />
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_340px]">
        <div className="panel p-5">
          <h2 className="font-bold">Runs and credits</h2>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%"><BarChart data={chart}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="day" /><YAxis /><Bar dataKey="runs" fill="#0f766e" /><Bar dataKey="credits" fill="#b7791f" /></BarChart></ResponsiveContainer>
          </div>
        </div>
        <div className="panel p-5">
          <h2 className="font-bold">Observability</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">Langfuse is {data.langfuse_enabled ? "enabled" : "disabled"}. Local structured timelines, tool logs, model usage, credits, and trace IDs remain available without private keys.</p>
          <div className="mt-4 rounded-md bg-slate-50 p-3 text-sm">Provider strategy: demo-local fallback, DeepSeek/Qwen/OpenAI-compatible later through ModelGateway.</div>
        </div>
      </div>
    </div>
  );
}
