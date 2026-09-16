import os
import json
import re
import logging
import urllib.request
import urllib.error
from models.schemas import GPUMetrics, AgentChatResponse
from gpu import diagnostics as diag

logger = logging.getLogger("GPUPilot.Agent")


def query_gemini_llm(metrics: GPUMetrics, query: str, api_key: str, model_name: str = "gemini-1.5-flash") -> AgentChatResponse | None:
    try:
        diagnosis = diag.analyse(metrics)
        b_type = diagnosis.bottleneck
        gpu_name = metrics.name or "GPU Accelerator"
        temp = metrics.temperature if metrics.temperature is not None else 65.0
        util = metrics.gpu_utilization if metrics.gpu_utilization is not None else 45.0
        vram = metrics.memory_utilization if metrics.memory_utilization is not None else 35.0
        vram_used = metrics.memory_used if metrics.memory_used is not None else 1.4
        vram_total = metrics.memory_total if metrics.memory_total is not None else 4.0
        cpu = metrics.cpu_utilization if metrics.cpu_utilization is not None else 30.0
        power = metrics.power_usage if metrics.power_usage is not None else 25.0
        power_limit = metrics.power_limit if metrics.power_limit is not None else 45.0
        gpu_clock = metrics.gpu_clock if metrics.gpu_clock is not None else 1350.0
        mem_clock = metrics.memory_clock if metrics.memory_clock is not None else 6000.0
        latency = metrics.latency if metrics.latency is not None else 22.0
        throughput = metrics.throughput if metrics.throughput is not None else 180.0

        system_instruction = (
            "You are GPUPilot, an autonomous AI GPU Performance Engineer and senior systems architect. "
            "You analyze real-time GPU telemetry and hardware metrics to provide deep, actionable engineering advice, "
            "bottleneck root-cause analysis, and optimization guidance. Keep your responses technically accurate, concise, "
            "grounded in the user's specific live metrics, and formatted in clean markdown. "
            "Always conclude your answer with a final line: 'ACTIONS: [Action 1, Action 2, Action 3]' with 2 to 4 concise action phrases."
        )

        prompt_body = (
            f"LIVE GPU TELEMETRY SNAPSHOT:\n"
            f"- Hardware Device: {gpu_name} (Vendor: {metrics.vendor})\n"
            f"- Compute Pipeline Load: {util:.1f}%\n"
            f"- VRAM Occupancy: {vram:.1f}% ({vram_used:.2f} GB used / {vram_total:.2f} GB total)\n"
            f"- GPU Core Temperature: {temp:.1f}°C\n"
            f"- Power Draw: {power:.1f}W (Target Limit: {power_limit:.1f}W)\n"
            f"- Core Clock: {gpu_clock:.0f} MHz | Memory Clock: {mem_clock:.0f} MHz\n"
            f"- Host CPU Load: {cpu:.1f}%\n"
            f"- Workload Latency: {latency:.1f} ms | Throughput: {throughput:.1f} ops/s\n"
            f"- Active Bottleneck Detection: {b_type.upper()} ({diagnosis.explanation})\n\n"
            f"USER QUESTION:\n\"{query}\""
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key.strip()}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "parts": [{"text": prompt_body}]
                }
            ],
            "generationConfig": {
                "temperature": 0.35,
                "maxOutputTokens": 900
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if not candidates:
                return None
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            if not text:
                return None

            actions = ["Run Sustained Benchmark", "Inspect Telemetry Metrics", "Apply Autonomous Tuner"]
            if "ACTIONS:" in text:
                parts = text.split("ACTIONS:")
                main_text = parts[0].strip()
                raw_acts = parts[1].strip().replace("[", "").replace("]", "").replace('"', '').replace("'", "")
                split_acts = [a.strip() for a in raw_acts.split(",") if a.strip()]
                if split_acts:
                    actions = split_acts[:4]
            else:
                main_text = text.strip()

            return AgentChatResponse(
                response=main_text,
                suggested_actions=actions,
                source=f"Google Gemini ({model_name})"
            )
    except Exception as e:
        logger.warning(f"Failed to query Gemini LLM ({e}), falling back to heuristic engine.")
        return None


def explain_state(metrics: GPUMetrics, query: str = "", api_key: str | None = None, model_name: str = "gemini-1.5-flash") -> AgentChatResponse:
    # Check if Gemini LLM key is provided or present in environment
    resolved_key = (api_key or "").strip() or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if resolved_key and query.strip():
        llm_resp = query_gemini_llm(metrics, query, resolved_key, model_name)
        if llm_resp:
            return llm_resp

    diagnosis = diag.analyse(metrics)
    b_type = diagnosis.bottleneck
    gpu_name = metrics.name or "GPU Accelerator"
    temp = metrics.temperature if metrics.temperature is not None else 65.0
    util = metrics.gpu_utilization if metrics.gpu_utilization is not None else 45.0
    vram = metrics.memory_utilization if metrics.memory_utilization is not None else 35.0
    vram_used = metrics.memory_used if metrics.memory_used is not None else 1.4
    vram_total = metrics.memory_total if metrics.memory_total is not None else 4.0
    cpu = metrics.cpu_utilization if metrics.cpu_utilization is not None else 30.0
    power = metrics.power_usage if metrics.power_usage is not None else 25.0
    power_limit = metrics.power_limit if metrics.power_limit is not None else 45.0
    gpu_clock = metrics.gpu_clock if metrics.gpu_clock is not None else 1350.0
    mem_clock = metrics.memory_clock if metrics.memory_clock is not None else 6000.0
    latency = metrics.latency if metrics.latency is not None else 22.0
    throughput = metrics.throughput if metrics.throughput is not None else 180.0

    q = (query or "").lower().strip()


    # 1. Performance / Speed / FPS / Latency / Throughput
    if any(k in q for k in ["performance", "speed", "fps", "how fast", "fast", "throughput", "latency", "tflops", "gflops", "rate"]):
        if util > 80 and temp < 85:
            perf_status = f"Your {gpu_name} is operating at **high compute efficiency** ({util:.0f}% load) at {gpu_clock:.0f} MHz."
            extra = f"Throughput is measuring ~{throughput:.1f} ops/sec with a low {latency:.1f} ms frame/dispatch latency. Tensor pipelines and CUDA cores are actively saturated."
        elif temp >= 85:
            perf_status = f"Performance on {gpu_name} is **degraded by thermal throttling** ({temp:.0f}°C)."
            extra = f"Core clocks have downclocked to {gpu_clock:.0f} MHz to prevent silicon damage. Dispatch latency has increased to {latency:.1f} ms."
        elif cpu > 75 and util < 40:
            perf_status = f"Performance is **starved by host CPU latency** (Host CPU: {cpu:.0f}% vs GPU: {util:.0f}%)."
            extra = f"The GPU is spending excessive cycles waiting for the CPU to process and dispatch batches. Frame latency is elevated at {latency:.1f} ms."
        else:
            perf_status = f"Your {gpu_name} is operating at a **moderate baseline** ({util:.0f}% load, {gpu_clock:.0f} MHz, {temp:.0f}°C)."
            extra = f"Current throughput is ~{throughput:.1f} ops/sec with {latency:.1f} ms latency. There is ample thermal and compute headroom available for heavier workloads."

        explanation = (
            f"📊 **Real-Time Performance Evaluation**\n\n"
            f"{perf_status} {extra}\n\n"
            f"• **Clock Speed**: {gpu_clock:.0f} MHz core / {mem_clock:.0f} MHz memory\n"
            f"• **Compute Pipeline**: {util:.0f}% utilized\n"
            f"• **Latency / Throughput**: {latency:.1f} ms / {throughput:.1f} ops/s\n\n"
            "**To Maximize Performance:** Enable PyTorch Automatic Mixed Precision (AMP FP16) to unlock Tensor Cores, compile your model with `torch.compile()`, and ensure AC power is connected."
        )
        actions = ["Enable FP16 Tensor Cores", "Compile with torch.compile()", "Run 10s Compute Benchmark"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 2. GPU Utilization / Usage / Load / Spikes
    is_util_query = (
        "utilization" in q
        or "gpu usage" in q
        or "gpu load" in q
        or "increases" in q
        or "increased" in q
        or "why high" in q
        or "why low" in q
        or (any(k in q for k in ["usage", "load", "spike"]) and not any(x in q for x in ["power", "watt", "vram", "memory", "cpu", "temp", "thermal"]))
    )
    if is_util_query:
        if util >= 80:
            util_analysis = (
                f"Your GPU utilization is currently high at **{util:.0f}%** on {gpu_name}. "
                "This indicates that your active workload (matrix multiplications, shader draw calls, or WebGL geometry) "
                "is fully saturating the Streaming Multiprocessors (SMs) and warp schedulers."
            )
            rec = (
                "If this is intentional (e.g. running a benchmark, model training, or 3D rendering), high utilization means you are getting full value from the silicon. "
                "If unexpected, check for background WebGL tabs or unthrottled render loops."
            )
        elif util <= 25:
            util_analysis = (
                f"Your GPU utilization is relatively low at **{util:.0f}%**. Meanwhile, host CPU is at {cpu:.0f}%."
            )
            rec = (
                "Low GPU utilization occurs when the GPU is idle or bottlenecked upstream by CPU preprocessing, I/O disk reads, "
                "or small batch sizes that underfill the CUDA execution warps."
            )
        else:
            util_analysis = (
                f"Your GPU utilization is in a balanced mid-range at **{util:.0f}%**. "
                "Workload batches are flowing smoothly through the graphics and compute queues."
            )
            rec = "Utilization fluctuates dynamically as kernels are launched and synchronized. Increasing batch size will push utilization higher toward 95%+ peak efficiency."

        explanation = (
            f"📈 **GPU Utilization Analysis**\n\n"
            f"{util_analysis}\n\n"
            f"**Why does GPU load change?**\n"
            "1. **Kernel Compute Density**: Operations like FP16 convolutions or matrix GEMMs push utilization to 99%.\n"
            "2. **Host Synchronization**: CPU transfers (`.to('cuda')`) or unpinned memory cause periodic dips in utilization.\n"
            "3. **Pipeline Bottlenecks**: When CPU or VRAM runs out, the GPU stalls waiting for data.\n\n"
            f"**Current Status:** {gpu_name} is running at **{util:.0f}%** load, drawing **{power:.1f}W** at **{temp:.0f}°C**.\n\n"
            f"**Advice:** {rec}"
        )
        actions = ["Tune Batch Size Multiplier", "Inspect Warp Occupancy", "Switch to Balanced Profile"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 3. CPU vs GPU / CPU Hotter / Starvation
    if ("cpu hotter" in q) or ("temp" in q and "cpu" in q) or ("cpu" in q and any(k in q for k in ["bottleneck", "starvation", "high", "hot", "usage", "100", "draw"])):
        explanation = (
            f"🖥️ **Host CPU vs Dedicated GPU Analysis**\n\n"
            f"Your host CPU ({cpu:.0f}% load) and {gpu_name} ({temp:.0f}°C, {util:.0f}% load) share a compact thermal chassis. "
            "In modern laptops, the CPU package frequently reaches 85-95°C during intensive tasks (such as 30,000 WebGL entity simulations or PyTorch DataLoader loops) "
            "while the dedicated GPU stays comparatively cooler (~60-70°C).\n\n"
            "**Why this happens:**\n"
            "• **Host Orchestration**: The CPU must calculate physics, transform geometry matrices, and submit draw calls to DirectX/OpenGL before the GPU can render a single frame.\n"
            "• **Thermal Mass**: CPU dies have smaller surface area and higher power density per mm² than the GPU die.\n"
            "• **Driver Stalls**: If single-threaded JS/Python is pegged at 100%, the GPU starves waiting for instructions.\n\n"
            "**Remediation:** Increase DataLoader `num_workers=4`, use page-locked memory (`pin_memory=True`), offload transforms to CUDA/WebGL shaders, and elevate the rear chassis."
        )
        actions = ["Parallelize Data Workers", "Enable Pin Memory", "Elevate Laptop Rear for Airflow"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 4. Memory / VRAM / 4GB / OOM
    if any(k in q for k in ["4gb", "vram", "memory", "oom", "out of memory", "allocation", "cache", "ram", "leak"]):
        explanation = (
            f"💾 **VRAM & Memory Management on {gpu_name}**\n\n"
            f"Current dedicated VRAM allocation is **{vram_used:.2f} GB / {vram_total:.2f} GB ({vram:.1f}%)**.\n\n"
            "On a 4GB accelerator, memory headroom is your strictest ceiling. VRAM is divided into:\n"
            "1. **Model Weights**: A 7B model in FP16 requires ~14GB (won't fit), but in 4-bit AWQ/GGUF requires only ~3.8GB.\n"
            "2. **Activations**: Scale linearly with batch size and quadratic with sequence length.\n"
            "3. **Optimizer States**: Adam requires 8 bytes per parameter in FP32.\n\n"
            "**Guaranteed Techniques to Avoid CUDA OOM:**\n"
            "• **Activation Checkpointing**: `model.gradient_checkpointing_enable()` discards intermediate activations during forward pass, cutting memory by up to 60%.\n"
            "• **Quantization**: Load with `load_in_8bit=True` or `load_in_4bit=True` via BitsAndBytes.\n"
            "• **Gradient Accumulation**: Simulate batch size 32 using micro-batch 4 accumulated over 8 steps.\n"
            "• **Cache Flush**: Call `torch.cuda.empty_cache()` after validation epochs."
        )
        actions = ["Enable Gradient Checkpointing", "Apply INT8/4-bit Quantization", "Cut Micro-Batch Size in Half"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 5. Temperature / Cooling / Fans / Thermal Throttle
    if any(k in q for k in ["temperature", "temp", "hot", "heat", "thermal", "cooling", "fan", "celsius", "overheat", "throttle"]):
        if temp >= 85:
            thermal_state = (
                f"⚠️ **Critical High Temperature ({temp:.0f}°C)**\n\n"
                f"Your {gpu_name} has crossed thermal throttling thresholds (85°C+). "
                "The silicon internal sensor is downclocking core frequencies to safeguard the die."
            )
            fix = "Immediately cap target power envelope by 15%, elevate the chassis, and verify fan exhaust vents are clear of obstructions."
        elif temp >= 72:
            thermal_state = (
                f"🌡️ **Elevated Temperature ({temp:.0f}°C)**\n\n"
                f"Your {gpu_name} is operating warm under sustained load. "
                "Dynamic boost clocks may begin stepping down slightly as temperature approaches 80°C."
            )
            fix = "Ensure adequate airflow under the laptop. Consider switching to the **Efficiency** profile to drop temps by 6-10°C with <5% frame loss."
        else:
            thermal_state = (
                f"❄️ **Optimal Thermal Envelope ({temp:.0f}°C)**\n\n"
                f"Your {gpu_name} is well below the 83°C thermal target. "
                "Fan acoustic levels and die temperatures are within healthy parameters."
            )
            fix = "You have ample thermal headroom to run intensive benchmarks or increase compute batch multiplier."

        fan_info = f"Fan Speed: {metrics.fan_speed:.0f}%" if metrics.fan_speed else "Fan Control: Laptop Embedded Controller (EC managed)"
        explanation = (
            f"{thermal_state}\n\n"
            f"• **Current Temp**: {temp:.0f}°C\n"
            f"• **{fan_info}**\n"
            f"• **Clock Speed**: {gpu_clock:.0f} MHz\n\n"
            f"**Thermal Recommendation:** {fix}"
        )
        actions = ["Apply Efficiency Profile (-15W)", "Elevate Chassis for Intake Air", "Run Thermal Stress Test"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 6. Power / Wattage / Battery / TGP
    if any(k in q for k in ["power", "watt", "tgp", "tdp", "battery", "energy", "consumption", "limit", "draw"]):
        p_pct = (power / power_limit * 100) if power_limit > 0 else 0
        explanation = (
            f"⚡ **Power & Energy Dynamics**\n\n"
            f"Your {gpu_name} is currently drawing **{power:.1f} Watts** against a target limit of **{power_limit:.1f} Watts** ({p_pct:.0f}% of TGP envelope).\n\n"
            "**Key Power Insights:**\n"
            "• **Dynamic Boost**: Modern laptop GPUs dynamically negotiate power with the CPU. When the CPU is heavily loaded, GPU power drops to prioritize host processing.\n"
            "• **Voltage-Frequency Curve**: Silicon power consumption scales with $V^2 \\times f$. Capping power by just 15% typically reduces temperatures by 8-12°C while sacrificing less than 3% compute throughput.\n"
            "• **Battery vs AC**: Always ensure your laptop is plugged into the OEM AC adapter; running on battery forces the GPU into low-power P8 state (clocks capped below 500 MHz)."
        )
        actions = ["Switch to Efficiency Profile", "Verify AC Power Connection", "Inspect TGP Ceiling"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 7. Clocks / Frequency / P-States
    if any(k in q for k in ["clock", "mhz", "frequency", "boost", "p-state", "core clock"]):
        explanation = (
            f"⏱️ **Clock Frequency Architecture**\n\n"
            f"Active Frequencies on {gpu_name}:\n"
            f"• **Core Clock**: **{gpu_clock:.0f} MHz**\n"
            f"• **Memory Clock**: **{mem_clock:.0f} MHz**\n\n"
            "**How GPU Clocks Work:**\n"
            "NVIDIA GPUs operate on automated P-States (P0 = Maximum 3D compute/CUDA, P8 = 2D Idle Desktop). "
            "The GPU Boost algorithm continuously evaluates three silicon limiters every millisecond: **Temperature**, **Power (TGP)**, and **Voltage reliability**. "
            "If temperature exceeds 75°C, clocks gradually step down in 15 MHz increments. If power reaches 45W, clock voltage is clamped."
        )
        actions = ["Check Thermal Margin", "Set High Performance Power Plan", "Run Compute Stress Test"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 8. Benchmark / Scoring / Testing
    if any(k in q for k in ["benchmark", "score", "grade", "test", "stress", "measure"]):
        explanation = (
            "🏆 **GPUPilot Composite Benchmarking Suite**\n\n"
            "GPUPilot grades your accelerator on a normalized scale from **0 to 1000 points** based on three live stress criteria:\n"
            "1. **Compute Sustained Throughput (40%)**: Tests raw FP32 / FP16 matrix operations and warp scheduling stability.\n"
            "2. **Thermal Resilience (35%)**: Measures temperature delta under full load. Systems that stay cool without thermal downclocking receive top marks.\n"
            "3. **Memory Bus Saturation (25%)**: Tests VRAM bandwidth transfer rates and cache eviction latency.\n\n"
            f"With your {gpu_name} running at **{util:.0f}%** load, **{temp:.0f}°C**, and **{power:.1f}W**, the system is primed for testing."
        )
        actions = ["Run 10s Sustained Benchmark", "Run Memory Bus Stress Test", "Compare Historical Grades"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 9. Optimization / Tuning / PyTorch / Code Remediation
    if any(k in q for k in ["optimize", "optimization", "tune", "tuning", "remediat", "improve", "fix", "faster", "code", "batch"]):
        explanation = (
            f"🛠️ **Autonomous Optimization Plan for {gpu_name}**\n\n"
            f"Based on current telemetry (Bottleneck: **{b_type.upper()}**, GPU: **{util:.0f}%**, VRAM: **{vram:.0f}%**, Temp: **{temp:.0f}°C**):\n\n"
            "**Top 3 Engineering Remediation Steps:**\n"
            "1. **Automatic Mixed Precision (AMP)**: Wrap forward pass in `torch.cuda.amp.autocast()` to use Tensor Cores. Yields 2x-3x speedup on Ampere architecture.\n"
            "2. **Kernel Fusion**: Use PyTorch 2.0 `model = torch.compile(model)` to fuse sequential elementwise kernels and eliminate CUDA launch overhead.\n"
            "3. **Zero-Copy Host Paging**: Set `DataLoader(..., pin_memory=True, num_workers=4)` to eliminate CPU memory copy stalls.\n\n"
            "You can also activate pre-tested profiles in the **Autonomous Tuner (Phase 10)** tab with 1-click execution."
        )
        actions = ["Apply Balanced Tuning Profile", "Copy PyTorch Remediation Code", "View Optimization Engine"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 10. Architecture / Specs / CUDA Cores
    if any(k in q for k in ["architecture", "spec", "specs", "cuda", "hardware", "device", "tensor core", "rtx"]):
        explanation = (
            f"⚙️ **Hardware Architecture & Specifications**\n\n"
            f"**Identified Device**: {gpu_name} ({metrics.vendor})\n"
            f"• **Silicon Generation**: NVIDIA Ampere Architecture (8nm GA107 Die)\n"
            f"• **Compute Units**: 2048 CUDA Cores, 64 Tensor Cores (3rd Gen), 16 RT Cores (2nd Gen)\n"
            f"• **Memory Subsystem**: {vram_total:.1f} GB GDDR6 on 128-bit bus (~192 GB/s bandwidth)\n"
            f"• **Power Envelope**: 35W - 60W Dynamic Boost TGP\n"
            f"• **Hardware Features**: FP16 Tensor Core acceleration, BF16 compute support, NVENC Gen 7 hardware video encoder."
        )
        actions = ["Test Tensor Core FP16 Ops", "Run 5s Compute Stress", "Check Active Telemetry"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 11. Bottleneck inquiries
    if any(k in q for k in ["bottleneck", "stall", "throttle", "constraint", "choke"]):
        explanation = (
            f"🔍 **Active Bottleneck Diagnostics**\n\n"
            f"GPUPilot's 6-rule heuristic engine evaluated your live telemetry and identified: **{b_type.upper()}**.\n\n"
            f"• **Severity Confidence**: {diagnosis.confidence * 100:.0f}%\n"
            f"• **Primary Metric**: {diagnosis.explanation}\n\n"
            f"**Hardware State Snapshot:**\n"
            f"- GPU Core Load: {util:.0f}%\n"
            f"- Memory Occupancy: {vram:.0f}% ({vram_used:.2f} / {vram_total:.2f} GB)\n"
            f"- Temperature: {temp:.0f}°C\n"
            f"- Host CPU: {cpu:.0f}%\n\n"
            f"Review the Remediation Plan tab for copy-paste PyTorch and system fixes."
        )
        actions = ["Open Optimization Tab", "Apply Autonomous Tuner", "Run Baseline Benchmark"]
        return AgentChatResponse(response=explanation, suggested_actions=actions)

    # 12. Smart Contextual Telemetry Breakdown (General Inquiries / Fallback)
    response = (
        f"🤖 **GPUPilot AI Telemetry Analysis for {gpu_name}**\n\n"
        f"I have inspected your real-time hardware telemetry in response to: *\"{query}\"*\n\n"
        f"• **Compute Load**: **{util:.0f}%** ({'High saturation' if util > 80 else 'Balanced workload' if util > 30 else 'Light/Idle'})\n"
        f"• **Thermals**: **{temp:.0f}°C** ({'Thermal throttle danger' if temp >= 85 else 'Normal operating range'})\n"
        f"• **VRAM Occupancy**: **{vram:.0f}%** ({vram_used:.2f} / {vram_total:.2f} GB)\n"
        f"• **Host CPU**: **{cpu:.0f}%** load\n"
        f"• **Active Bottleneck**: **{b_type.replace('_', ' ').title()}**\n\n"
        "Ask me specific questions like *'Why is my GPU utilization increasing?'*, *'How to reduce temperature?'*, or *'What is performance?'* for deep-dive root cause analysis!"
    )
    actions = ["Explain Active Bottleneck", "Run Sustained Benchmark", "Apply Tuning Profile"]
    return AgentChatResponse(response=response, suggested_actions=actions)
