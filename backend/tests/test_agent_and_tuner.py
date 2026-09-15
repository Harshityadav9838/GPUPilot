# Tests for Phase 9 (AI Agent Explainer) and Phase 10 (Autonomous Tuner)
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from models.schemas import GPUMetrics, ApplyTuningRequest
from gpu import agent
from gpu import tuner


def _mock_metrics(bottleneck_type="healthy") -> GPUMetrics:
    if bottleneck_type == "thermal":
        return GPUMetrics(vendor="NVIDIA", name="RTX 3050", temperature=92.0, gpu_utilization=85.0)
    elif bottleneck_type == "vram":
        return GPUMetrics(vendor="NVIDIA", name="RTX 3050", memory_utilization=96.0, memory_used=3.9, memory_total=4.0)
    elif bottleneck_type == "cpu":
        return GPUMetrics(vendor="NVIDIA", name="RTX 3050", cpu_utilization=90.0, gpu_utilization=20.0)
    return GPUMetrics(vendor="NVIDIA", name="RTX 3050", temperature=60.0, gpu_utilization=40.0, memory_utilization=25.0)


def test_ai_agent_explanation_thermal():
    m = _mock_metrics("thermal")
    res = agent.explain_state(m)
    assert "thermal" in res.response.lower()
    assert len(res.suggested_actions) >= 1


def test_ai_agent_explanation_custom_query():
    m = _mock_metrics("healthy")
    res = agent.explain_state(m, "Why is my CPU hotter than my GPU?")
    assert "chassis" in res.response.lower() or "cpu" in res.response.lower()


def test_tuner_get_profiles():
    profiles = tuner.get_profiles()
    assert len(profiles) == 3
    ids = [p.id for p in profiles]
    assert "balanced" in ids
    assert "efficiency" in ids
    assert "performance" in ids


def test_tuner_apply_dry_run():
    req = ApplyTuningRequest(profile_id="efficiency", dry_run=True)
    res = tuner.apply_profile(req)
    assert res.status == "success"
    assert res.dry_run is True
    assert res.applied_settings["power_target_percent"] == 80


def test_tuner_apply_real():
    req = ApplyTuningRequest(profile_id="performance", dry_run=False)
    res = tuner.apply_profile(req)
    assert res.status == "success"
    assert res.dry_run is False
