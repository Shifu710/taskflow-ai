from app.core.config import settings


def model_gateway(prompt: str, purpose: str) -> dict:
    provider = settings.ai_provider or "demo-local"
    if not settings.ai_api_key or provider == "demo-local":
        return {
            "provider": "demo-local",
            "model": "demo-local",
            "text": f"Demo-local {purpose}: {prompt[:220]}",
            "prompt_tokens": max(80, len(prompt) // 4),
            "completion_tokens": 160,
            "credits": 1.5,
            "simulated": True,
        }
    return {
        "provider": provider,
        "model": settings.ai_model,
        "text": f"Provider placeholder for {purpose}.",
        "prompt_tokens": max(80, len(prompt) // 4),
        "completion_tokens": 160,
        "credits": 2.0,
        "simulated": False,
    }
