import { useEffect, useState } from "react";
import { getDashboard } from "../services/dashboardApi";

const TYPE_ICONS = {
  conversation: "Chat",
  document: "File",
  memory: "Memory",
  update: "Update",
};

function StatCard({ icon, label, value }) {
  return (
    <div className="dashboard-stat-card">
      <div className="dashboard-stat-icon">{icon}</div>
      <div className="dashboard-stat-value">{value}</div>
      <div className="dashboard-stat-label">{label}</div>
    </div>
  );
}

function DashboardPanel({ onNavigate }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard()
      .then((res) => setData(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-loading">
          <div className="dashboard-loading-core"></div>
          <span>Loading AI Twin intelligence...</span>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="dashboard-page">
        <div className="dashboard-error">
          Unable to load dashboard.
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">

      <div className="dashboard-hero">
        <div>
          <div className="dashboard-eyebrow">
            <span className="dashboard-live-dot"></span>
            AI TWIN OVERVIEW
          </div>

          <h1>Dashboard</h1>

          <p>
            A live snapshot of everything your AI Twin knows,
            remembers, and has done.
          </p>
        </div>

        <div className="dashboard-core-mini">
          <span>AI</span>
        </div>
      </div>

      <div className="dashboard-stats">
        <StatCard
          icon="Chat"
          label="Conversations"
          value={data.totals.conversations}
        />

        <StatCard
          icon="Memory"
          label="Memories"
          value={data.totals.memories}
        />

        <StatCard
          icon="File"
          label="Documents"
          value={data.totals.documents}
        />

        <StatCard
          icon="Skill"
          label="Skills"
          value={data.totals.skills}
        />

        <StatCard
          icon="Project"
          label="Projects"
          value={data.totals.projects}
        />
      </div>

      <div className="dashboard-grid">

        <section className="dashboard-panel dashboard-graph-panel">
          <div className="dashboard-panel-header">
            <div>
              <span className="dashboard-panel-kicker">
                KNOWLEDGE
              </span>
              <h2>Knowledge Graph</h2>
            </div>

            <div className="dashboard-panel-badge">
              {data.graph_summary.total_facts} facts
            </div>
          </div>

          <p className="dashboard-panel-description">
            Connected information currently stored across your
            AI Twin knowledge graph.
          </p>

          <div className="dashboard-big-number">
            {data.graph_summary.total_categories}
            <span> categories</span>
          </div>

          <div className="dashboard-category-list">
            {Object.entries(data.graph_summary.by_category || {}).map(
              ([cat, count]) => (
                <div className="dashboard-category-row" key={cat}>
                  <span>
                    {cat.replace("_", " ")}
                  </span>
                  <strong>{count}</strong>
                </div>
              )
            )}
          </div>

          {onNavigate && (
            <button
              className="dashboard-action"
              onClick={() => onNavigate("graph")}
            >
              Explore Graph
              <span>→</span>
            </button>
          )}
        </section>

        <section className="dashboard-panel dashboard-profile-panel">
          <div className="dashboard-panel-header">
            <div>
              <span className="dashboard-panel-kicker">
                IDENTITY
              </span>
              <h2>Profile</h2>
            </div>

            <div className="dashboard-profile-orb">
              P
            </div>
          </div>

          <div className="dashboard-big-number">
            {data.profile_summary.total_facts}
            <span> verified facts</span>
          </div>

          <div className="dashboard-profile-status">
            <span className="profile-status-icon">✓</span>
            <span>
              {data.profile_summary.sections_present.join(", ") ||
                "No profile sections yet"}
            </span>
          </div>

          {data.profile_summary.sections_missing.length > 0 && (
            <div className="dashboard-missing">
              <span>Not yet known</span>
              <p>
                {data.profile_summary.sections_missing.join(", ")}
              </p>
            </div>
          )}

          {onNavigate && (
            <button
              className="dashboard-action"
              onClick={() => onNavigate("profile")}
            >
              Open Profile
              <span>→</span>
            </button>
          )}
        </section>

      </div>

      <section className="dashboard-panel dashboard-activity-panel">

        <div className="dashboard-panel-header">
          <div>
            <span className="dashboard-panel-kicker">
              LIVE MEMORY
            </span>
            <h2>Recent Activity</h2>
          </div>

          <div className="dashboard-activity-count">
            {data.recent_activity.length} events
          </div>
        </div>

        {data.recent_activity.length === 0 ? (
          <div className="dashboard-empty-activity">
            Nothing yet.
          </div>
        ) : (
          <div className="dashboard-activity-list">
            {data.recent_activity.map((event, i) => (
              <div
                className="dashboard-activity-row"
                key={i}
              >
                <div className="dashboard-activity-icon">
                  {TYPE_ICONS[event.type] || "•"}
                </div>

                <div className="dashboard-activity-content">
                  <span>{event.title}</span>
                  <small>{event.type || "activity"}</small>
                </div>

                <time>{event.date}</time>
              </div>
            ))}
          </div>
        )}

        {onNavigate && (
          <button
            className="dashboard-action dashboard-timeline-action"
            onClick={() => onNavigate("timeline")}
          >
            View Full Timeline
            <span>→</span>
          </button>
        )}

      </section>

    </div>
  );
}

export default DashboardPanel;
