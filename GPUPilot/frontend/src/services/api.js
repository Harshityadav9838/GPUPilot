const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = {
  async getHealth() {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  },

  async getGPU() {
    const res = await fetch(`${BASE_URL}/gpu`);
    if (!res.ok) throw new Error(`Failed to fetch GPU info: ${res.statusText}`);
    return res.json();
  },

  async getMetrics() {
    const res = await fetch(`${BASE_URL}/metrics`);
    if (!res.ok) throw new Error(`Failed to fetch metrics: ${res.statusText}`);
    return res.json();
  },

  async getScenarios() {
    const res = await fetch(`${BASE_URL}/demo/scenarios`);
    if (!res.ok) throw new Error(`Failed to fetch scenarios: ${res.statusText}`);
    return res.json();
  },

  async setScenario(scenario) {
    const res = await fetch(`${BASE_URL}/demo/scenario`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario }),
    });
    if (!res.ok) throw new Error(`Failed to change scenario: ${res.statusText}`);
    return res.json();
  },

  async getDiagnosis() {
    const res = await fetch(`${BASE_URL}/diagnose`);
    if (!res.ok) throw new Error(`Failed to fetch diagnosis: ${res.statusText}`);
    return res.json();
  }
};
