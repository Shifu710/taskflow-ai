"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { Activity, Boxes, ChartNoAxesCombined, ClipboardCheck, Home, KeyRound, Settings, Workflow, Wrench } from "lucide-react";

const items = [
  { label: "Dashboard", segment: "dashboard", icon: Home },
  { label: "Workflows", segment: "workflows", icon: Workflow },
  { label: "Runs", segment: "runs", icon: Activity },
  { label: "Tools", segment: "tools", icon: Wrench },
  { label: "Approvals", segment: "approvals", icon: ClipboardCheck },
  { label: "Usage", segment: "usage", icon: ChartNoAxesCombined },
  { label: "Settings", segment: "settings", icon: Settings }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const params = useParams<{ workspaceId: string }>();
  const pathname = usePathname();
  const workspaceId = params.workspaceId ?? "ws_demo";
  return (
    <div className="min-h-screen bg-slate-100">
      <aside className="fixed inset-y-0 left-0 hidden w-72 border-r border-line bg-white p-4 lg:block">
        <Link href="/" className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-md bg-accent text-sm font-bold text-white">TF</span>
          <span>
            <span className="block font-bold text-ink">TaskFlow AI</span>
            <span className="text-xs text-slate-500">Agent workflow automation</span>
          </span>
        </Link>
        <nav className="mt-8 grid gap-1">
          {items.map((item) => {
            const href = `/workspaces/${workspaceId}/${item.segment}`;
            const Icon = item.icon;
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link key={item.segment} href={href} className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm ${active ? "bg-teal-50 text-accent" : "text-slate-600 hover:bg-slate-50"}`}>
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-4 left-4 right-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <div className="flex items-center gap-2 font-semibold"><KeyRound size={16} /> Demo-safe mode</div>
          <p className="mt-2">External writes and live web research are simulated. Runtime state, approvals, tool calls, credits, and usage logs are real local records.</p>
        </div>
      </aside>
      <main className="min-h-screen lg:pl-72">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-white/95 px-4 py-3 backdrop-blur lg:px-8">
          <Link className="font-bold lg:hidden" href="/">TaskFlow AI</Link>
          <div className="hidden text-sm text-slate-500 lg:block">TaskFlow Demo Workspace</div>
          <div className="flex items-center gap-3">
            <Link className="btn-secondary" href="/technical-review">Technical Review</Link>
            <Link className="btn-secondary" href="/workspaces">Workspaces</Link>
          </div>
        </header>
        <div className="p-4 lg:p-8">{children}</div>
      </main>
    </div>
  );
}

export function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="panel p-4">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-2 text-2xl font-bold text-ink">{value}</div>
    </div>
  );
}

export function StatusPill({ status }: { status: string }) {
  const tone = status === "completed" ? "border-emerald-200 bg-emerald-50 text-emerald-700" : status.includes("waiting") ? "border-amber-200 bg-amber-50 text-amber-700" : status === "failed" ? "border-rose-200 bg-rose-50 text-rose-700" : "border-slate-200 bg-slate-50 text-slate-700";
  return <span className={`status-pill ${tone}`}>{status}</span>;
}
