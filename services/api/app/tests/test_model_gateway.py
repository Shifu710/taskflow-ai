from app.runtime.model_gateway import model_gateway


def test_model_gateway_uses_demo_local_without_provider_keys():
    result = model_gateway("Research Bytebase", "planner")
    assert result["provider"] == "demo-local"
    assert result["simulated"] is True
    assert result["credits"] > 0
