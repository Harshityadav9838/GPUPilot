import React, { useState, useEffect } from "react";
import { Sliders, ShieldCheck, Check, Sparkles, AlertCircle } from "lucide-react";
import { api } from "../services/api";

export function TuningPanel() {
  const [profiles, setProfiles] = useState([]);
  const [activeProfile, setActiveProfile] = useState("balanced");
  const [feedback, setFeedback] = useState(null);
  const [isApplying, setIsApplying] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const list = await api.getTuningProfiles();
        setProfiles(list);
      } catch (e) {
        console.error("Could not load tuning profiles:", e);
      }
    }
    load();
  }, []);

  const handleApply = async (profileId, dryRun = false) => {
    setIsApplying(true);
    setFeedback(null);
    try {
      const res = await api.applyTuningProfile(profileId, dryRun);
      if (!dryRun) setActiveProfile(profileId);
      setFeedback({
        type: "success",
        msg: res.message,
        snippet: res.applied_settings.py_config_snippet
      });
    } catch (err) {
      setFeedback({ type: "error", msg: err.message });
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="glass-card tuning-card">
      <div className="tuning-header">
        <div className="flex-row items-center gap-2">
          <div className="tuning-icon-badge">
            <Sliders size={18} className="text-emerald" />
          </div>
          <div>
            <div className="tuning-title">Autonomous Tuning & Profile Applier (Phase 10)</div>
            <div className="tuning-subtitle">
              Verified operating envelopes for thermals, acoustic comfort, and maximum compute throughput
            </div>
          </div>
        </div>
        <div className="active-profile-pill">
          Active: <strong>{activeProfile.toUpperCase()}</strong>
        </div>
      </div>

      {feedback && (
        <div className={`tuning-feedback-banner ${feedback.type}`}>
          <div className="flex-row items-center gap-2">
            {feedback.type === "success" ? <ShieldCheck size={16} /> : <AlertCircle size={16} />}
            <span>{feedback.msg}</span>
          </div>
          {feedback.snippet && (
            <pre className="tuning-snippet-code"><code>{feedback.snippet}</code></pre>
          )}
        </div>
      )}

      <div className="tuning-profiles-grid">
        {profiles.map((p) => {
          const isSelected = activeProfile === p.id;
          return (
            <div key={p.id} className={`profile-card ${isSelected ? "selected" : ""}`}>
              <div className="profile-top">
                <span className="profile-name">{p.name}</span>
                {isSelected && <span className="profile-active-tag">Active</span>}
              </div>
              <p className="profile-desc">{p.description}</p>

              <div className="profile-meta-row">
                <span>Power: <strong>{p.target_power_percent}%</strong></span>
                <span>Batch: <strong>{p.recommended_batch_multiplier}x</strong></span>
              </div>

              <div className="profile-features-list">
                {p.features.map((feat, idx) => (
                  <div key={idx} className="feat-item">
                    <Check size={12} className="text-emerald" />
                    <span>{feat}</span>
                  </div>
                ))}
              </div>

              <div className="profile-actions">
                <button
                  className="btn-dry-run"
                  onClick={() => handleApply(p.id, true)}
                  disabled={isApplying}
                  title="Simulate settings without applying changes"
                >
                  Dry-Run Verify
                </button>
                <button
                  className={`btn-apply-profile ${isSelected ? "applied" : ""}`}
                  onClick={() => handleApply(p.id, false)}
                  disabled={isApplying || isSelected}
                >
                  {isSelected ? "Active Profile" : "Apply Parameters"}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
