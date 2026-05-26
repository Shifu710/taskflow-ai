import Link from "next/link";
import { ArrowRight, Bot, ClipboardCheck, GitBranch, ShieldCheck, Wrench, type LucideIcon } from "lucide-react";

const features: Array<[string, string, LucideIcon]> = [
  ["LangGraph runtime", "Stateful workflow runs with persisted steps, pause/resume, retries, and final output validation.", GitBranch],
  ["Tool gateway", "MCP-style discovery and schema-validated invocation with auditable tool-call logs.", Wrench],
  ["Human approval", "Approval gates stop execution before sensitive actions and resume with a recorded decision.", ClipboardCheck],
  ["AgentOps", "Usage logs, credits, latency, model/provider metadata, and local Langfuse-ready traces.", Bot],
  ["RBAC safety", "Workspace roles protect workflow editing, tool management, approvals, and guest demo boundaries.", ShieldCheck]
];

export default function Home() {
  return (
    <main>
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <Link className="flex items-center gap-3 font-bold" href="/">
          <span className="grid h-10 w-10 place-items-center rounded-md bg-accent text-white">TF</span>
          TaskFlow AI
        </Link>
        <div className="flex gap-3">
          <Link className="btn-secondary" href="/technical-review">Technical Review</Link>
          <Link className="btn-primary" href="/demo">Try Guest Demo</Link>
        </div>
      </nav>
      <section className="mx-auto grid max-w-7xl gap-10 px-6 py-14 lg:grid-cols-[1fr_.85fr]">
        <div>
          <p className="inline-flex rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-sm font-medium text-accent">Enterprise AI Agent Workflow Automation</p>
          <h1 className="mt-6 text-4xl font-black tracking-tight text-ink md:text-6xl">Design, run, approve, and audit AI agent workflows.</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">TaskFlow AI proves real agent workflow automation: LangGraph orchestration, tool calling, human approval gates, live execution traces, retries, cost controls, usage logs, RBAC, and a working guest demo.</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link className="btn-primary" href="/demo">Try Guest Demo <ArrowRight size={18} /></Link>
            <Link className="btn-secondary" href="/login">Login</Link>
          </div>
          <p className="mt-6 text-sm text-slate-500">Chinese positioning: 企业级 AI Agent 工作流自动化平台，支持状态机、工具调用、人审节点、实时轨迹、成本控制和 AgentOps 可观测性。</p>
        </div>
        <div className="panel p-5">
          <div className="text-sm font-semibold text-slate-500">Live demo scenario</div>
          <h2 className="mt-2 text-2xl font-bold text-ink">Competitor Research & Outreach Agent</h2>
          <div className="mt-5 grid gap-3">
            {["Planner step starts", "Demo tools execute", "Approval gate pauses", "User approves", "Reviewer completes", "Structured report appears", "Credits and usage logs update"].map((item, index) => (
              <div key={item} className="flex items-center gap-3 rounded-md border border-line bg-slate-50 p-3">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-white text-sm font-bold text-accent">{index + 1}</span>
                <span className="text-sm">{item}</span>
              </div>
            ))}
          </div>
        </div>
      </section>
      <section className="mx-auto grid max-w-7xl gap-4 px-6 pb-16 md:grid-cols-2 lg:grid-cols-5">
        {features.map(([title, description, Icon]) => (
          <div className="panel p-4" key={title}>
            <Icon className="text-accent" />
            <h3 className="mt-3 font-bold text-ink">{title}</h3>
            <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
          </div>
        ))}
      </section>
    </main>
  );
}
