const serviceApiBase = process.env.NEXT_PUBLIC_API_URL
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
  : undefined;

const configuredApiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? serviceApiBase;

const isBrowser = typeof window !== "undefined";
const isLocalBrowser =
  isBrowser &&
  ["localhost", "127.0.0.1"].includes(window.location.hostname);

export const API_BASE =
  configuredApiBase ?? (isLocalBrowser ? "http://localhost:8000/api/v1" : "");
export const DEMO_WORKSPACE_ID = "ws_demo";
export const DEMO_WORKFLOW_ID = "wf_competitor";

function getApiBase() {
  if (!API_BASE) {
    throw new Error(
      "TaskFlow API is not configured. Set NEXT_PUBLIC_API_BASE_URL to the deployed FastAPI backend URL, for example https://taskflow-ai-api.onrender.com/api/v1."
    );
  }

  return API_BASE;
}

export function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("taskflow_token") ?? "";
}

export function setToken(token: string) {
  localStorage.setItem("taskflow_token", token);
  document.cookie = `taskflow_session=${token}; path=/; max-age=604800; SameSite=Lax`;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();

  let res: Response;
  try {
    res = await fetch(`${getApiBase()}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init.headers ?? {})
      },
      cache: "no-store"
    });
  } catch {
    throw new Error(
      `Could not reach TaskFlow API at ${getApiBase()}. Check that the FastAPI backend is deployed, healthy, CORS allows this frontend, and NEXT_PUBLIC_API_BASE_URL is set correctly in Vercel.`
    );
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export type Workflow = {
  id: string;
  name: string;
  description: string;
  status: string;
  version: number;
  definition_json: { steps: Array<{ id: string; type: string; tool?: string; message?: string }> };
  guest_read_only?: boolean;
};

export type RunDetail = {
  run: {
    id: string;
    workflow_id: string;
    status: string;
    input_json: Record<string, unknown>;
    final_output_json: null | Record<string, unknown>;
    error_json: null | Record<string, unknown>;
    current_step_id: string | null;
    credits_used: number;
    prompt_tokens: number;
    completion_tokens: number;
    tool_calls_count: number;
    runtime_ms: number;
    trace_id: string;
  };
  steps: Array<{ id: string; step_id: string; step_type: string; status: string; output_json: unknown; retry_count: number; latency_ms: number }>;
  tool_calls: Array<{ id: string; step_id: string; tool_name: string; status: string; output_json: unknown; retry_count: number; latency_ms: number }>;
  approvals: Array<{ id: string; run_id: string; step_id: string; status: string; message: string; payload_json: unknown }>;
};
