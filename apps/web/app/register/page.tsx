"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { API_BASE, setToken } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [workspaceName, setWorkspaceName] = useState("My TaskFlow Workspace");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, name, password, workspace_name: workspaceName })
    });
    if (!res.ok) {
      setError(await res.text());
      setBusy(false);
      return;
    }
    const data = await res.json() as { token: string; workspaces: Array<{ id: string }> };
    setToken(data.token);
    router.push(`/workspaces/${data.workspaces[0].id}/dashboard`);
  }

  return (
    <main className="grid min-h-screen place-items-center px-6">
      <form className="panel w-full max-w-md p-6" onSubmit={submit}>
        <h1 className="text-2xl font-bold">Create workspace</h1>
        <p className="mt-3 text-slate-600">Create an owner account and a private TaskFlow workspace. The public demo remains available without registration.</p>
        <label className="mt-5 block text-sm font-semibold">Name</label>
        <input className="mt-2 w-full rounded-md border border-line px-3 py-2" value={name} onChange={(event) => setName(event.target.value)} required />
        <label className="mt-4 block text-sm font-semibold">Email</label>
        <input className="mt-2 w-full rounded-md border border-line px-3 py-2" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        <label className="mt-4 block text-sm font-semibold">Password</label>
        <input className="mt-2 w-full rounded-md border border-line px-3 py-2" type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required />
        <label className="mt-4 block text-sm font-semibold">Workspace</label>
        <input className="mt-2 w-full rounded-md border border-line px-3 py-2" value={workspaceName} onChange={(event) => setWorkspaceName(event.target.value)} required />
        {error ? <p className="mt-4 rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
        <button className="btn-primary mt-6 w-full justify-center" disabled={busy}>{busy ? "Creating..." : "Register"}</button>
        <div className="mt-4 flex justify-between text-sm">
          <Link className="text-accent" href="/demo">Try Guest Demo</Link>
          <Link className="text-slate-500" href="/login">Login</Link>
        </div>
      </form>
    </main>
  );
}
