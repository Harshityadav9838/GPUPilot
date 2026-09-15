import { webEngine } from "./webEngine";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

let isBackendAvailable = null;

async function checkBackend() {
  if (isBackendAvailable !== null) return isBackendAvailable;
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1200);
    const res = await fetch(`${BASE_URL}/health`, { signal: controller.signal });
    clearTimeout(timeout);
    isBackendAvailable = res.ok;
  } catch (e) {
    isBackendAvailable = false;
  }
  return isBackendAvailable;
}

export const api = {
  isWebMode() {
    return isBackendAvailable === false;
  },

  async getHealth() {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/health`);
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.getHealth();
  },

  async getGPU() {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/gpu`);
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.getGPU();
  },

  async getMetrics() {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/metrics`);
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.getMetrics();
  },

  async getScenarios() {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/demo/scenarios`);
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.getScenarios();
  },

  async setScenario(scenario) {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/demo/scenario`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scenario }),
        });
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.setScenario(scenario);
  },

  async switchMode(mode) {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/provider/mode`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode }),
        });
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return { status: "success", active_mode: mode, is_demo: true };
  },

  async getDiagnosis() {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/diagnose`);
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.getDiagnosis();
  },

  async getOptimizationPlan() {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/optimize`);
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.getOptimizationPlan();
  },

  async runBenchmark(test_type = "compute", duration_seconds = 5) {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/benchmark/run`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ test_type, duration_seconds }),
        });
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.runBenchmark(test_type, duration_seconds);
  },

  async getBenchmarkStatus() {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/benchmark/status`);
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.getBenchmarkStatus();
  },

  async getBenchmarkHistory() {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/benchmark/history`);
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.getBenchmarkHistory();
  },

  async askAgent(prompt) {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/agent/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt }),
        });
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.askAgent(prompt);
  },

  async getTuningProfiles() {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/tuner/profiles`);
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.getTuningProfiles();
  },

  async applyTuningProfile(profile_id, dry_run = false) {
    if (await checkBackend()) {
      try {
        const res = await fetch(`${BASE_URL}/tuner/apply`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ profile_id, dry_run }),
        });
        if (res.ok) return res.json();
      } catch (e) {
        isBackendAvailable = false;
      }
    }
    return webEngine.applyTuningProfile(profile_id, dry_run);
  }
};
