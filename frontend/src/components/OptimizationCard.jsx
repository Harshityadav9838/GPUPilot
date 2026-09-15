import React, { useState } from "react";
import { Wrench, Copy, Check, ExternalLink, Zap, TrendingUp } from "lucide-react";

export function OptimizationCard({ plan }) {
  const [copiedId, setCopiedId] = useState(null);

  if (!plan || !plan.recommendations || plan.recommendations.length === 0) {
    return null;
  }

  const handleCopy = (id, text) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getImpactBadgeClass = (impact) => {
    switch (impact?.toLowerCase()) {
      case "critical": return "impact-critical";
      case "high": return "impact-high";
      case "medium": return "impact-medium";
      default: return "impact-low";
    }
  };

  return (
    <div className="glass-card optimization-card">
      <div className="opt-header">
        <div className="flex-row items-center gap-2">
          <div className="opt-icon-badge">
            <Wrench size={18} className="text-cyan" />
          </div>
          <div>
            <div className="opt-title">Optimization Engineering Prescriptions</div>
            <div className="opt-subtitle">
              Targeted code and configuration remediations for current workload state
            </div>
          </div>
        </div>
        <div className="opt-count-badge">
          {plan.recommendations.length} Action{plan.recommendations.length > 1 ? "s" : ""} Available
        </div>
      </div>

      <div className="opt-list">
        {plan.recommendations.map((rec) => (
          <div key={rec.id} className="opt-item">
            <div className="opt-item-top">
              <div className="flex-row items-center gap-2">
                <span className={`impact-badge ${getImpactBadgeClass(rec.impact)}`}>
                  {rec.impact} Impact
                </span>
                <span className="category-tag">{rec.category}</span>
              </div>
              {rec.doc_url && (
                <a
                  href={rec.doc_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="doc-link"
                  title="Open official documentation"
                >
                  <span>Docs</span>
                  <ExternalLink size={12} />
                </a>
              )}
            </div>

            <div className="opt-item-title">{rec.title}</div>
            <p className="opt-item-summary">{rec.summary}</p>

            {rec.estimated_gain && (
              <div className="opt-gain-row">
                <TrendingUp size={14} className="text-emerald" />
                <span><strong>Expected Gain:</strong> {rec.estimated_gain}</span>
              </div>
            )}

            {rec.code_snippet && (
              <div className="opt-snippet-box">
                <div className="snippet-top">
                  <span className="snippet-label">Remediation Snippet</span>
                  <button
                    className="btn-copy"
                    onClick={() => handleCopy(rec.id, rec.code_snippet)}
                    title="Copy code to clipboard"
                  >
                    {copiedId === rec.id ? (
                      <>
                        <Check size={13} className="text-emerald" />
                        <span className="text-emerald">Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy size={13} />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
                <pre className="snippet-code">
                  <code>{rec.code_snippet}</code>
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
