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


def test_ai_agent_distinct_answers_for_different_queries():
    m = _mock_metrics("healthy")
    res_perf = agent.explain_state(m, "now what is performance")
    res_util = agent.explain_state(m, "why my gpu utilization increases")
    res_power = agent.explain_state(m, "what is my power usage")
    res_vram = agent.explain_state(m, "how to fit into 4gb vram")

    # Responses must be distinctly different from each other
    assert res_perf.response != res_util.response
    assert res_util.response != res_power.response
    assert res_power.response != res_vram.response

    # Verify domain-specific content
    assert "performance" in res_perf.response.lower() or "evaluation" in res_perf.response.lower()
    assert "utilization" in res_util.response.lower() or "streaming multiprocessors" in res_util.response.lower()
    assert "power" in res_power.response.lower() or "watts" in res_power.response.lower()
    assert "vram" in res_vram.response.lower() or "checkpointing" in res_vram.response.lower()



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
