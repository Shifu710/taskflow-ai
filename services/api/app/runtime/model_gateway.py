import time

import httpx

from app.core.config import settings


def model_gateway(prompt: str, purpose: str) -> dict:
    candidates = provider_candidates()
    for candidate in candidates:
        if not candidate["api_key"]:
            continue
        try:
            return call_openai_compatible(
                provider=candidate["provider"],
                model=candidate["model"],
                base_url=candidate["base_url"],
                api_key=candidate["api_key"],
                prompt=prompt,
                purpose=purpose,
            )
        except Exception:
            continue
    return demo_local(prompt, purpose)


def provider_candidates() -> list[dict]:
    requested = (settings.ai_provider or "demo-local").lower()
    providers = [
        {
            "provider": "deepseek",
            "model": settings.deepseek_model,
            "base_url": "https://api.deepseek.com/v1",
            "api_key": settings.deepseek_api_key or (settings.ai_api_key if requested == "deepseek" else None),
        },
        {
            "provider": "qwen",
            "model": settings.qwen_model,
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "api_key": settings.qwen_api_key or (settings.ai_api_key if requested == "qwen" else None),
        },
        {
            "provider": "openai-compatible",
            "model": settings.openai_compatible_model if requested != "openai-compatible" else settings.ai_model,
            "base_url": settings.openai_compatible_base_url,
            "api_key": settings.openai_compatible_api_key or (settings.ai_api_key if requested in {"openai", "openai-compatible"} else None),
        },
    ]
    if requested in {"deepseek", "qwen", "openai", "openai-compatible"}:
        providers.sort(key=lambda item: item["provider"] != ("openai-compatible" if requested == "openai" else requested))
    return providers


def call_openai_compatible(provider: str, model: str, base_url: str, api_key: str, prompt: str, purpose: str) -> dict:
    started = time.perf_counter()
    response = httpx.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": f"You are TaskFlow AI's {purpose} node. Return concise, structured business output."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    usage = data.get("usage") or {}
    text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    prompt_tokens = int(usage.get("prompt_tokens") or max(80, len(prompt) // 4))
    completion_tokens = int(usage.get("completion_tokens") or max(80, len(text) // 4))
    return {
        "provider": provider,
        "model": model,
        "text": text,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "credits": estimate_credits(prompt_tokens, completion_tokens),
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "simulated": False,
    }


def demo_local(prompt: str, purpose: str) -> dict:
    return {
        "provider": "demo-local",
        "model": "demo-local",
        "text": f"Demo-local {purpose}: {prompt[:220]}",
        "prompt_tokens": max(80, len(prompt) // 4),
        "completion_tokens": 160,
        "credits": 1.5,
        "latency_ms": 120,
        "simulated": True,
    }


def estimate_credits(prompt_tokens: int, completion_tokens: int) -> float:
    return round(max(0.5, ((prompt_tokens + completion_tokens) / 1000) * 2), 2)
