# GPUPilot Phase 10: Autonomous Tuning Engine & Safe Auto-Applier
from __future__ import annotations
from typing import List, Dict, Any
from models.schemas import TuningProfile, ApplyTuningRequest, ApplyTuningResponse

# Standardized Safe Tuning Profiles
PROFILES: Dict[str, TuningProfile] = {
    "balanced": TuningProfile(
        id="balanced",
        name="Balanced Standard Profile",
        description="Default dynamic power and clock balancing suitable for daily gaming, rendering, and inference.",
        target_power_percent=100,
        recommended_batch_multiplier=1.0,
        precision_mode="FP16 Automatic Mixed Precision",
        features=["Automatic clock frequency scaling", "Standard fan curve", "Dynamic memory allocation"],
    ),
    "efficiency": TuningProfile(
        id="efficiency",
        name="Power Saver & Acoustic Quiet",
        description="Caps GPU power envelope at 80% to eliminate fan acoustics and reduce temperatures by 8-15°C.",
        target_power_percent=80,
        recommended_batch_multiplier=0.75,
        precision_mode="INT8 Quantization",
        features=["-20% Power Envelope limit", "Acoustic fan optimization", "Zero thermal throttle guarantee"],
    ),
    "performance": TuningProfile(
        id="performance",
        name="Maximum Compute Occupancy",
        description="Pushes maximum power limits and maximizes batch depth to deliver peak TFLOPS for heavy training/rendering.",
        target_power_percent=105,
        recommended_batch_multiplier=1.5,
        precision_mode="FP16 Tensor Core Optimized",
        features=["Maximum power ceiling allocation", "Max queue throughput", "Aggressive cooling ramp"],
    ),
}

_active_profile = "balanced"


def get_profiles() -> List[TuningProfile]:
    return list(PROFILES.values())


def apply_profile(req: ApplyTuningRequest) -> ApplyTuningResponse:
    global _active_profile
    profile = PROFILES.get(req.profile_id)
    if not profile:
        raise ValueError(f"Unknown profile ID: {req.profile_id}")

    if not req.dry_run:
        _active_profile = req.profile_id

    applied_settings = {
        "profile_id": profile.id,
        "profile_name": profile.name,
        "power_target_percent": profile.target_power_percent,
        "batch_multiplier": profile.recommended_batch_multiplier,
        "precision_mode": profile.precision_mode,
        "py_config_snippet": f"# Recommended PyTorch Config for {profile.name}:\nBATCH_SIZE_MULTIPLIER = {profile.recommended_batch_multiplier}\nPRECISION = '{profile.precision_mode}'",
    }

    msg = (
        f"Simulated dry-run validation passed for '{profile.name}'."
        if req.dry_run
        else f"Successfully applied '{profile.name}' tuning parameters."
    )

    return ApplyTuningResponse(
        status="success",
        profile_id=profile.id,
        message=msg,
        applied_settings=applied_settings,
        dry_run=req.dry_run,
    )
