# GPUPilot Phase 6: Optimization Recommendation Engine
# Translates BottleneckResult into rich actionable optimization prescriptions.
from __future__ import annotations
from typing import List
from models.schemas import (
    GPUMetrics,
    OptimizationRecommendation,
    OptimizationPlanResponse,
)
from gpu import diagnostics as diag


def generate_plan(metrics: GPUMetrics) -> OptimizationPlanResponse:
    diagnosis = diag.analyse(metrics)
    b_type = diagnosis.bottleneck
    recs: List[OptimizationRecommendation] = []

    if b_type == diag.THERMAL_THROTTLE:
        recs = [
            OptimizationRecommendation(
                id="thermal_power_cap",
                category="Hardware & Thermal",
                title="Enforce Dynamic Power Cap (NVIDIA NVML / nvidia-smi)",
                summary="Throttle power target down by 10-15% to immediately halt thermal runaway with <3% throughput degradation.",
                impact="Critical",
                estimated_gain="Drops junction temp by 6-12°C while preserving steady clock frequencies",
                code_snippet="nvidia-smi -pl 40  # Temporarily clamp power limit to 40W\n# Or in Python with pynvml:\n# pynvml.nvmlDeviceSetPowerManagementLimit(handle, 40000)",
                doc_url="https://docs.nvidia.com/deploy/nvml-api/group__nvmlDeviceQueries.html",
            ),
            OptimizationRecommendation(
                id="thermal_fan_profile",
                category="Cooling",
                title="Set Aggressive Fan Curve / Max Cooling Mode",
                summary="Engage maximum chassis exhaust fans early to prevent heat soak on shared laptop heatpipes.",
                impact="High",
                estimated_gain="Prevents clock throttling from 1700 MHz down to baseline 210 MHz",
                code_snippet="# In MyASUS or OEM control panel:\n# Set Fan Profile -> 'Performance' or 'Full Speed Mode'",
                doc_url="https://www.asus.com/support/FAQ/1042747/",
            ),
        ]
    elif b_type == diag.VRAM_EXHAUSTION:
        recs = [
            OptimizationRecommendation(
                id="vram_batch_downscale",
                category="Memory & Batching",
                title="Downscale Micro-Batch Size & Enable Gradient Accumulation",
                summary="Halve forward pass batch size while accumulating gradients over multiple steps to preserve effective batch size.",
                impact="Critical",
                estimated_gain="Frees ~40-50% dedicated VRAM immediately, eliminating OOM hazard",
                code_snippet="# PyTorch training loop optimization:\ntrain_loader = DataLoader(dataset, batch_size=batch_size // 2)\n\nfor i, (inputs, targets) in enumerate(train_loader):\n    loss = model(inputs, targets) / accum_steps\n    loss.backward()\n    if (i + 1) % accum_steps == 0:\n        optimizer.step()\n        optimizer.zero_grad()",
                doc_url="https://pytorch.org/docs/stable/notes/amp_examples.html#gradient-accumulation",
            ),
            OptimizationRecommendation(
                id="vram_grad_checkpointing",
                category="PyTorch Memory",
                title="Enable Activation Checkpointing (Gradient Checkpointing)",
                summary="Discard intermediate activations during forward pass and recompute them on backward pass to drastically compress memory footprint.",
                impact="High",
                estimated_gain="Saves 60-70% activation VRAM for LLM and Transformer layers",
                code_snippet="model.gradient_checkpointing_enable()\n# Or in HuggingFace transformers:\n# training_args = TrainingArguments(..., gradient_checkpointing=True)",
                doc_url="https://pytorch.org/docs/stable/checkpoint.html",
            ),
            OptimizationRecommendation(
                id="vram_quantization",
                category="Model Compression",
                title="Apply INT8 / FP8 Post-Training Quantization or LoRA",
                summary="Load weights in 8-bit precision instead of FP32 or FP16 for inference or PEFT training.",
                impact="High",
                estimated_gain="Cuts model weights VRAM in half with negligible loss of perplexity/accuracy",
                code_snippet="from transformers import AutoModelForCausalLM, BitsAndBytesConfig\n\nbnb_config = BitsAndBytesConfig(load_in_8bit=True)\nmodel = AutoModelForCausalLM.from_pretrained('model_name', quantization_config=bnb_config)",
                doc_url="https://huggingface.co/docs/bitsandbytes/main/en/index",
            ),
        ]
    elif b_type == diag.COMPUTE_BOUND:
        recs = [
            OptimizationRecommendation(
                id="compute_amp_fp16",
                category="Compute & Precision",
                title="Enable Automatic Mixed Precision (AMP FP16 / BF16)",
                summary="Execute matrix multiplications and convolutions in Tensor Cores using FP16 / BF16 while maintaining FP32 master weights.",
                impact="High",
                estimated_gain="Up to 2x - 3x faster tensor throughput on NVIDIA RTX Tensor Cores",
                code_snippet="import torch\nscaler = torch.cuda.amp.GradScaler()\n\nwith torch.cuda.amp.autocast(dtype=torch.float16):\n    outputs = model(inputs)\n    loss = criterion(outputs, targets)\n\nscaler.scale(loss).backward()\nscaler.step(optimizer)\nscaler.update()",
                doc_url="https://pytorch.org/docs/stable/amp.html",
            ),
            OptimizationRecommendation(
                id="compute_torch_compile",
                category="Kernel Fusion",
                title="Compile Model with TorchDynamo (torch.compile)",
                summary="JIT-compiles PyTorch graphs into fused Triton kernels, reducing memory roundtrips and maximizing compute occupancy.",
                impact="High",
                estimated_gain="15-40% lower execution latency on modern GPU architectures",
                code_snippet="import torch\n\n# Compile model using Inductor backend:\noptimized_model = torch.compile(model, mode='reduce-overhead')",
                doc_url="https://pytorch.org/tutorials/intermediate/torch_compile_tutorial.html",
            ),
            OptimizationRecommendation(
                id="compute_batch_saturation",
                category="Occupancy",
                title="Increase Workload Queue Depth & Batch Size",
                summary="Ensure Tensor Cores remain fully saturated across all Streaming Multiprocessors (SMs) by increasing evaluation batch sizes.",
                impact="Medium",
                estimated_gain="Amortizes kernel launch overheads and maximizes TFLOPS efficiency",
                code_snippet="# Ensure tensor dimensions are multiples of 8 or 16 for Tensor Core alignment:\nbatch_size = ((requested_batch + 7) // 8) * 8",
                doc_url="https://docs.nvidia.com/deeplearning/performance/mixed-precision-training/index.html#tensor-core-requirements",
            ),
        ]
    elif b_type == diag.CPU_STARVATION:
        recs = [
            OptimizationRecommendation(
                id="cpu_dataloader_workers",
                category="Data Pipeline",
                title="Parallelize DataLoader Batch Preparation with Multi-Workers",
                summary="Allocate background subprocesses for image/audio/token data transformation so GPU is never starved waiting for the next batch.",
                impact="High",
                estimated_gain="Removes GPU idle dips; boosts GPU utilization from ~20% up to 85%+",
                code_snippet="from torch.utils.data import DataLoader\n\nloader = DataLoader(\n    dataset,\n    batch_size=32,\n    num_workers=4,       # Use 4-8 background CPU workers\n    pin_memory=True,     # Fast page-locked host memory transfers\n    persistent_workers=True\n)",
                doc_url="https://pytorch.org/docs/stable/data.html#multi-process-data-loading",
            ),
            OptimizationRecommendation(
                id="cpu_gpu_decoding",
                category="Hardware Acceleration",
                title="Offload Preprocessing to NVIDIA DALI / TorchVision GPU Transforms",
                summary="Move image resizing, JPEG decoding, and normalization directly onto GPU CUDA cores, freeing host CPU cycles entirely.",
                impact="High",
                estimated_gain="Reduces host CPU load by 50-70% and cuts batch ingestion latency",
                code_snippet="# Moving transforms to GPU tensor operations:\nimport torchvision.transforms.v2 as transforms\n\ngpu_transforms = torch.nn.Sequential(\n    transforms.Resize((224, 224)),\n    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])\n).cuda()\n\n# Run directly on GPU batch tensor:\nimages = gpu_transforms(raw_batch.cuda(non_blocking=True))",
                doc_url="https://docs.nvidia.com/deeplearning/dali/user-guide/docs/index.html",
            ),
        ]
    elif b_type == diag.MEMORY_BANDWIDTH:
        recs = [
            OptimizationRecommendation(
                id="mem_flash_attention",
                category="Kernel Optimization",
                title="Replace Standard Attention with FlashAttention-2",
                summary="Computes exact softmax attention using tiled SRAM blocks without materializing large N x N intermediate attention matrices in HBM.",
                impact="Critical",
                estimated_gain="2x - 4x speedup in LLM attention layers; cuts memory traffic by 80%",
                code_snippet="# HuggingFace Transformers integration:\nmodel = AutoModelForCausalLM.from_pretrained(\n    'model_id',\n    torch_dtype=torch.float16,\n    attn_implementation='flash_attention_2'\n)",
                doc_url="https://github.com/Dao-AILab/flash-attention",
            ),
            OptimizationRecommendation(
                id="mem_fused_ops",
                category="Memory Layout",
                title="Fuse Pointwise Operations & Ensure Tensor Contiguity",
                summary="Avoid fragmented memory reads by calling .contiguous() prior to view operations, and fusing LayerNorm/GELU with cuDNN/Triton.",
                impact="Medium",
                estimated_gain="Eliminates redundant global memory roundtrips and improves bandwidth utilization",
                code_snippet="# Combine memory operations:\nx = torch.nn.functional.layer_norm(x, normalized_shape).contiguous()",
                doc_url="https://pytorch.org/docs/stable/generated/torch.Tensor.contiguous.html",
            ),
        ]
    elif b_type == diag.VRAM_PRESSURE:
        recs = [
            OptimizationRecommendation(
                id="vram_empty_cache",
                category="Memory Management",
                title="Prune PyTorch Memory Allocator Fragmentation Cache",
                summary="Release unused cached blocks held by the caching allocator back to the OS when transitioning between workloads.",
                impact="Medium",
                estimated_gain="Reclaims fragmented memory buffers without resetting Python runtime",
                code_snippet="import gc, torch\ngc.collect()\ntorch.cuda.empty_cache()\n# Print exact memory summary:\nprint(torch.cuda.memory_summary())",
                doc_url="https://pytorch.org/docs/stable/generated/torch.cuda.empty_cache.html",
            ),
            OptimizationRecommendation(
                id="vram_eval_no_grad",
                category="Inference Optimization",
                title="Wrap Inference Pipelines in torch.inference_mode()",
                summary="Completely disables autograd tracking, version counters, and view metadata tracking to minimize tensor overhead.",
                impact="Medium",
                estimated_gain="Saves 15-25% memory overhead and speeds up evaluation passes",
                code_snippet="with torch.inference_mode():\n    predictions = model(eval_batch)",
                doc_url="https://pytorch.org/docs/stable/generated/torch.inference_mode.html",
            ),
        ]
    else:  # HEALTHY / NONE
        recs = [
            OptimizationRecommendation(
                id="healthy_baseline",
                category="Monitoring & Telemetry",
                title="Baseline Profiling & Regression Safeguards",
                summary="Current GPU and CPU operations are operating within peak thermal, memory, and compute envelopes. Establish golden benchmarks.",
                impact="Low",
                estimated_gain="Ensures regression-free continuous inference deployment",
                code_snippet="# Log baseline metrics for drift detection:\nwith open('baseline_telemetry.json', 'w') as f:\n    json.dump(metrics.model_dump(), f, indent=2)",
                doc_url="https://github.com/NVIDIA/gpu-monitoring-tools",
            )
        ]

    return OptimizationPlanResponse(
        bottleneck=diagnosis.bottleneck,
        status=diagnosis.status,
        severity=diagnosis.severity,
        recommendations=recs,
    )
