import { useEffect, useState } from "react";
import { getProfile } from "../services/profileApi";

const SECTION_ICONS = {
  personal: "👤",
  education: "🎓",
  career: "💼",
  experience: "🧳",
  project: "🛠️",
  technical_skill: "💻",
  achievement: "🏆",
  goal: "🎯",
  preference: "❤️",
  contact: "📇",
  other: "📌",
};

function ConfidenceDot({ confidence }) {
  const value = typeof confidence === "number" ? confidence : 0.7;
  const color = value >= 0.8 ? "#28a745" : value >= 0.5 ? "#ffc107" : "#dc3545";
  return (
    <span
      title={`${Math.round(value * 100)}% confidence`}
      style={{
        display: "inline-block",
        width: "8px",
        height: "8px",
        borderRadius: "50%",
        background: color,
        marginRight: "8px",
      }}
    />
  );
}

function ProfilePanel({ onEditMemories }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProfile()
      .then((res) => setProfile(res.data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div style={{ padding: "30px", color: "#888" }}>Loading profile...</div>;
  }

  if (!profile || profile.sections.length === 0) {
    return (
      <div style={{ padding: "30px" }}>
        <h1>👤 AI Twin Profile</h1>
        <p style={{ color: "#aaa" }}>
          Nothing to show yet — your profile is built automatically from what your
          AI Twin has learned about you. Chat with it or upload documents, and this
          page will fill in on its own.
        </p>
      </div>
    );
  }

  return (
    <div style={{ padding: "30px", width: "100%", overflowY: "auto" }}>
      <h1 style={{ marginBottom: "6px" }}>👤 AI Twin Profile</h1>
      <p style={{ color: "#aaa", marginBottom: "10px" }}>
        Built automatically from {profile.total_facts} verified memories. Nothing here
        is invented — every line traces back to something you told your AI Twin or a
        document it read. To correct anything, edit it in the Memory Center.
      </p>

      {onEditMemories && (
        <button
          onClick={onEditMemories}
          style={{
            background: "#007bff", color: "white", border: "none",
            padding: "8px 16px", borderRadius: "6px", cursor: "pointer",
            marginBottom: "25px",
          }}
        >
          ✏ Edit in Memory Center
        </button>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
          gap: "18px",
        }}
      >
        {profile.sections.map((section) => (
          <div
            key={section.type}
            style={{
              background: "#40414f",
              borderRadius: "10px",
              padding: "18px 20px",
            }}
          >
            <h3 style={{ margin: "0 0 12px 0" }}>
              {SECTION_ICONS[section.type] || "📌"} {section.label}
            </h3>

            {section.items.map((item) => (
              <div key={item.id} style={{ marginBottom: "10px", color: "white" }}>
                <p style={{ margin: 0, fontSize: "14px" }}>
                  <ConfidenceDot confidence={item.confidence} />
                  {item.text}
                </p>
                {item.source && (
                  <p style={{ margin: "2px 0 0 16px", color: "#888", fontSize: "11px" }}>
                    via {item.source}
                  </p>
                )}
              </div>
            ))}
          </div>
        ))}
      </div>

      {profile.missing_sections.length > 0 && (
        <div style={{ marginTop: "25px", color: "#777", fontSize: "13px" }}>
          Not yet known: {profile.missing_sections.map((s) => s.label).join(", ")}
        </div>
      )}
    </div>
  );
}

export default ProfilePanel;
