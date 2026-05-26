"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("demo@taskflow.ai");
  const [password, setPassword] = useState("demo12345");
  const [error, setError] = useState("");

  async function submit() {
    try {
      const res = await api<{ token: string; workspaces: Array<{ id: string }> }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
      setToken(res.token);
      router.push(`/workspaces/${res.workspaces[0].id}/dashboard`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    }
  }

  return (
    <main className="grid min-h-screen place-items-center px-6">
      <div className="panel w-full max-w-md p-6">
        <p className="text-sm text-accent">TaskFlow AI</p>
        <h1 className="mt-2 text-3xl font-bold">Login</h1>
        <p className="mt-2 text-sm text-slate-500">Demo owner: demo@taskflow.ai / demo12345</p>
        <div className="mt-6 grid gap-3">
          <input className="rounded-md border border-line px-3 py-2" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="rounded-md border border-line px-3 py-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          <button className="btn-primary" onClick={submit}>Login</button>
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          <Link className="text-sm text-accent" href="/demo">Use guest demo instead</Link>
          <Link className="text-sm text-slate-500" href="/">Back home</Link>
        </div>
      </div>
    </main>
  );
}
