export default function SettingsPage() {
  return (
    <div>
      <h1 className="text-3xl font-bold">Workspace Settings</h1>
      <div className="panel mt-6 p-5">
        <h2 className="font-bold">Cost and loop limits</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {["max_run_steps: 20", "max_run_cost_credits: 50", "max_tool_calls_per_run: 20", "max_runtime_seconds: 120", "default_model: demo-local"].map((item) => <div className="rounded-md bg-slate-50 p-3 text-sm" key={item}>{item}</div>)}
        </div>
        <p className="mt-4 text-sm text-slate-600">Guest mode cannot modify workspace settings. Production deployments should connect this page to owner/admin-only update APIs.</p>
      </div>
    </div>
  );
}
