DEMO_COMPANIES = {
    "bytebase": {
        "name": "Bytebase",
        "category": "Database DevOps",
        "market": "Developer tooling",
        "signals": ["open-source adoption", "enterprise compliance", "team approval flows"],
        "source": "seeded-demo-data",
    },
    "taskflow": {
        "name": "TaskFlow AI",
        "category": "Agent workflow automation",
        "market": "AI operations",
        "signals": ["human approval gates", "tool calling", "AgentOps dashboards"],
        "source": "seeded-demo-data",
    },
}


def demo_search(payload: dict) -> dict:
    if payload.get("force_retry_once") and not payload.get("_retried"):
        payload["_retried"] = True
        raise ValueError("Simulated transient search failure")
    query = payload["query"].lower()
    matches = [value for key, value in DEMO_COMPANIES.items() if key in query or value["name"].lower() in query]
    if not matches:
        matches = [DEMO_COMPANIES["bytebase"]]
    return {"results": matches, "query": payload["query"], "source": "seeded-demo-data"}


def company_profile_lookup(payload: dict) -> dict:
    company = payload["company"].lower()
    base = DEMO_COMPANIES.get(company, DEMO_COMPANIES["bytebase"])
    return {
        "company": base["name"],
        "profile": f"{base['name']} operates in {base['market']} with a focus on {base['category']}.",
        "buying_triggers": base["signals"],
        "recommended_angle": "Lead with operational reliability, approval controls, and measurable usage logging.",
        "source": "seeded-demo-data",
    }


def calculator(payload: dict) -> dict:
    expression = payload["expression"]
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        raise ValueError("Only arithmetic expressions are allowed in demo calculator.")
    return {"result": eval(expression, {"__builtins__": {}}, {})}


def csv_analyzer(payload: dict) -> dict:
    rows = payload.get("rows", [])
    return {"row_count": len(rows), "columns": list(rows[0].keys()) if rows else [], "insight": "Demo CSV analysis completed."}


def passthrough_demo(payload: dict) -> dict:
    return {"accepted": True, "simulated": True, "payload": payload}


TOOL_FUNCTIONS = {
    "demo_search": demo_search,
    "company_profile_lookup": company_profile_lookup,
    "calculator": calculator,
    "csv_analyzer": csv_analyzer,
    "document_lookup_demo": passthrough_demo,
    "http_request_demo": passthrough_demo,
    "webhook_sender_demo": passthrough_demo,
    "email_draft_generator": passthrough_demo,
    "create_ticket_demo": passthrough_demo,
    "crm_note_writer_demo": passthrough_demo,
    "task_creator_demo": passthrough_demo,
}
