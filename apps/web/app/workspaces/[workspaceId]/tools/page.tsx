"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Tool = { id: string; name: string; slug: string; description: string; tool_type: string; enabled: boolean; requires_approval: boolean; max_retries: number };

export default function ToolsPage() {
  const { workspaceId } = useParams<{ workspaceId: string }>();
  const [tools, setTools] = useState<Tool[]>([]);
  const [manifest, setManifest] = useState<unknown>(null);
  useEffect(() => {
    api<{ tools: Tool[] }>(`/workspaces/${workspaceId}/tools`).then((res) => setTools(res.tools));
    api(`/workspaces/${workspaceId}/mcp/tools`).then(setManifest);
  }, [workspaceId]);
  return (
    <div>
      <h1 className="text-3xl font-bold">Tool Registry</h1>
      <p className="mt-2 text-slate-600">Schema-validated tools exposed through an internal MCP-style gateway. Guest mode only sees demo-safe tools.</p>
      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_420px]">
        <div className="grid gap-3">
          {tools.map((tool) => (
            <div className="panel p-4" key={tool.id}>
              <div className="flex items-center justify-between"><h2 className="font-bold">{tool.name}</h2><span className="text-sm text-slate-500">{tool.tool_type}</span></div>
              <p className="mt-2 text-sm text-slate-600">{tool.description}</p>
              <div className="mt-3 text-xs text-slate-500">slug: {tool.slug} / retries: {tool.max_retries} / approval: {tool.requires_approval ? "required" : "not required"}</div>
            </div>
          ))}
        </div>
        <div className="panel p-5">
          <h2 className="font-bold">MCP-style manifest</h2>
          <pre className="mt-3 max-h-[520px] overflow-auto rounded-md bg-slate-950 p-3 text-xs text-slate-100">{JSON.stringify(manifest, null, 2)}</pre>
        </div>
      </div>
    </div>
  );
}
