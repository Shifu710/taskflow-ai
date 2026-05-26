import Link from "next/link";

export default function RegisterPage() {
  return (
    <main className="grid min-h-screen place-items-center px-6">
      <div className="panel max-w-md p-6">
        <h1 className="text-2xl font-bold">Register</h1>
        <p className="mt-3 text-slate-600">Public portfolio mode keeps registration disabled. Use the guest demo or demo owner account to explore the working workflow runtime.</p>
        <div className="mt-6 flex gap-3">
          <Link className="btn-primary" href="/demo">Try Guest Demo</Link>
          <Link className="btn-secondary" href="/login">Login</Link>
        </div>
      </div>
    </main>
  );
}
