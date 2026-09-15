import { webEngine } from "./webEngine";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

let isBackendLive = false;

// Helper to attempt backend request with graceful fallback
async function fetchWithFallback(endpoint, options = {}) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (res.ok) {
      isBackendLive = true;
      return await res.json();
    }
  } catch (e) {
    // Backend not reachable
  }
  return null;
}

export const api = {
  isWebMode() {
    return !isBackendLive;
  },

  async getHealth() {
    const data = await fetchWithFallback("/health");
    if (data) return data;
    return webEngine.getHealth();
  },

  async getGPU() {
    const data = await fetchWithFallback("/gpu");
    if (data) return data;
    return webEngine.getGPU();
  },

  async getMetrics() {
    const data = await fetchWithFallback("/metrics");
    if (data) return data;
    return webEngine.getMetrics();
  },

  async getScenarios() {
    const data = await fetchWithFallback("/demo/scenarios");
    if (data) return data;
    return webEngine.getScenarios();
  },

  async setScenario(scenario) {
    const data = await fetchWithFallback("/demo/scenario", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario }),
    });
    if (data) return data;
    return webEngine.setScenario(scenario);
  },

  async switchMode(mode) {
    // Always attempt real backend first for mode switching
    try {
      const res = await fetch(`${BASE_URL}/provider/mode`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode }),
      });
      if (res.ok) {
        isBackendLive = true;
        return await res.json();
      }
    } catch (e) {
      console.warn("Backend unavailable during mode switch, using web mode.");
    }
    // If on Vercel or backend completely stopped
    return {
      status: "success",
      active_mode: mode,
      is_demo: mode !== "hardware",
      gpu_name: mode === "hardware" ? "NVIDIA GeForce RTX 3050 (Direct Web)" : "Simulator"
    };
  },

  async getDiagnosis() {
    const data = await fetchWithFallback("/diagnose");
    if (data) return data;
    return webEngine.getDiagnosis();
  },

  async getOptimizationPlan() {
    const data = await fetchWithFallback("/optimize");
    if (data) return data;
    return webEngine.getOptimizationPlan();
  },

  async runBenchmark(test_type = "compute", duration_seconds = 5) {
    const data = await fetchWithFallback("/benchmark/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ test_type, duration_seconds }),
    });
    if (data) return data;
    return webEngine.runBenchmark(test_type, duration_seconds);
  },

  async getBenchmarkStatus() {
    const data = await fetchWithFallback("/benchmark/status");
    if (data) return data;
    return webEngine.getBenchmarkStatus();
  },

  async getBenchmarkHistory() {
    const data = await fetchWithFallback("/benchmark/history");
    if (data) return data;
    return webEngine.getBenchmarkHistory();
  },

  async askAgent(prompt) {
    const data = await fetchWithFallback("/agent/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    if (data) return data;
    return webEngine.askAgent(prompt);
  },

  async getTuningProfiles() {
    const data = await fetchWithFallback("/tuner/profiles");
    if (data) return data;
    return webEngine.getTuningProfiles();
  },

  async applyTuningProfile(profile_id, dry_run = false) {
    const data = await fetchWithFallback("/tuner/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile_id, dry_run }),
    });
    if (data) return data;
    return webEngine.applyTuningProfile(profile_id, dry_run);
  }
};
