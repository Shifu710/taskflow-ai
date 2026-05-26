import Link from "next/link";

export default function AdminPage() {
  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="text-3xl font-bold">Admin</h1>
      <div className="panel mt-6 p-5">
        <p className="text-slate-600">Admin operations are intentionally limited in public demo mode. Owner/admin APIs exist for RBAC enforcement; destructive workspace and tool operations should be enabled only after production auth hardening.</p>
        <Link className="btn-primary mt-4" href="/demo">Open guest demo</Link>
      </div>
    </main>
  );
}
