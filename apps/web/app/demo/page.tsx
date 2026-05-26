"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";

export default function DemoPage() {
  const router = useRouter();
  const [error, setError] = useState("");

  useEffect(() => {
    api<{ token: string; workspace_id: string }>("/auth/guest", { method: "POST", body: "{}" })
      .then((res) => {
        setToken(res.token);
        router.replace(`/workspaces/${res.workspace_id}/dashboard`);
      })
      .catch((err) => setError(err.message));
  }, [router]);

  return (
    <main className="grid min-h-screen place-items-center px-6">
      <div className="panel max-w-md p-6 text-center">
        <h1 className="text-2xl font-bold">Opening guest demo</h1>
        <p className="mt-3 text-slate-600">Signing in as guest@taskflow.ai and loading the demo workspace.</p>
        {error ? <p className="mt-4 text-sm text-rose-600">{error}</p> : null}
      </div>
    </main>
  );
}
