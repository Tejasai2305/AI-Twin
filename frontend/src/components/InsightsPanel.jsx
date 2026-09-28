import { useEffect, useState } from "react";
import { getInsights } from "../services/insightsApi";

const SEVERITY_META = {
  high: {
    label: "HIGH PRIORITY",
    className: "insight-high",
  },
  medium: {
    label: "REVIEW",
    className: "insight-medium",
  },
  low: {
    label: "LOW PRIORITY",
    className: "insight-low",
  },
};

const TYPE_META = {
  duplicate_memory: { icon: "MEMORY", label: "Memory" },
  low_confidence_facts: { icon: "FACT", label: "Confidence" },
  profile_gap: { icon: "PROFILE", label: "Profile" },
  unindexed_document: { icon: "FILE", label: "Document" },
  missing_document_file: { icon: "FILE", label: "Document" },
  recent_contradiction: { icon: "CHECK", label: "Consistency" },
};

function InsightsPanel({ onNavigate }) {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getInsights()
      .then((res) => setInsights(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const targetPage = {
    duplicate_memory: "memory",
    low_confidence_facts: "memory",
    recent_contradiction: "memory",
    profile_gap: "profile",
    unindexed_document: "documents",
    missing_document_file: "documents",
  };

  const highCount = insights.filter((item) => item.severity === "high").length;
  const mediumCount = insights.filter((item) => item.severity === "medium").length;
  const lowCount = insights.filter((item) => item.severity === "low").length;

  return (
    <div className="insights-page">
      <div className="insights-hero">
        <div>
          <div className="insights-eyebrow">
            <span className="insights-live-dot"></span>
            AI TWIN ANALYSIS
          </div>

          <h1>Insights</h1>

          <p>
            Suggestions based on patterns detected across your memories,
            profile and documents. You decide what to do with each one.
          </p>
        </div>

        <div className="insights-core-mini">
          <span>AI</span>
        </div>
      </div>

      <div className="insights-summary">
        <div className="insight-summary-card">
          <span className="insight-summary-label">TOTAL</span>
          <strong>{insights.length}</strong>
          <small>Insights detected</small>
        </div>

        <div className="insight-summary-card insight-summary-high">
          <span className="insight-summary-label">HIGH</span>
          <strong>{highCount}</strong>
          <small>Needs attention</small>
        </div>

        <div className="insight-summary-card insight-summary-medium">
          <span className="insight-summary-label">REVIEW</span>
          <strong>{mediumCount}</strong>
          <small>Worth checking</small>
        </div>

        <div className="insight-summary-card insight-summary-low">
          <span className="insight-summary-label">LOW</span>
          <strong>{lowCount}</strong>
          <small>Minor observations</small>
        </div>
      </div>

      <section className="insights-panel">
        <div className="insights-panel-header">
          <div>
            <span className="insights-panel-kicker">DETECTED PATTERNS</span>
            <h2>What your AI Twin noticed</h2>
          </div>

          <div className="insights-count">
            {insights.length} {insights.length === 1 ? "insight" : "insights"}
          </div>
        </div>

        {loading ? (
          <div className="insights-loading">
            <div className="insights-loading-core"></div>
            <span>Analyzing your AI Twin...</span>
          </div>
        ) : insights.length === 0 ? (
          <div className="insights-empty">
            <div className="insights-empty-core">✓</div>
            <h3>Everything looks clean</h3>
            <p>
              Nothing needs to be flagged right now. New insights will appear
              here as your AI Twin learns more.
            </p>
          </div>
        ) : (
          <div className="insights-list">
            {insights.map((insight, i) => {
              const severity =
                SEVERITY_META[insight.severity] || SEVERITY_META.low;

              const type =
                TYPE_META[insight.type] || {
                  icon: "INSIGHT",
                  label: "Insight",
                };

              return (
                <div
                  key={i}
                  className={`insight-card ${severity.className}`}
                >
                  <div className="insight-severity-line"></div>

                  <div className="insight-type-icon">
                    {type.icon}
                  </div>

                  <div className="insight-content">
                    <div className="insight-meta">
                      <span className="insight-type-label">
                        {type.label}
                      </span>

                      <span className="insight-severity-label">
                        {severity.label}
                      </span>
                    </div>

                    <p>{insight.message}</p>
                  </div>

                  {onNavigate && targetPage[insight.type] && (
                    <button
                      className="insight-review-button"
                      onClick={() => onNavigate(targetPage[insight.type])}
                    >
                      Review
                      <span>→</span>
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

export default InsightsPanel;
