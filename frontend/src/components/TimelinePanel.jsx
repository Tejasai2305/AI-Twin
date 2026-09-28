import { useEffect, useState } from "react";
import { getTimeline, getTimelineYears, getTimelineCategories } from "../services/timelineApi";

const TYPE_ICONS = {
  conversation: "💬",
  document: "📄",
  memory: "🧠",
  update: "🔁",
};

const CATEGORY_COLORS = {
  personal: "#6f42c1",
  education: "#0d6efd",
  career: "#20c997",
  technical_skill: "#fd7e14",
  project: "#e83e8c",
  preference: "#6610f2",
  goal: "#17a2b8",
  achievement: "#ffc107",
  experience: "#28a745",
  contact: "#6c757d",
  conversation: "#3f51b5",
  document: "#795548",
  other: "#495057",
};

function TimelinePanel() {
  const [events, setEvents] = useState([]);
  const [years, setYears] = useState([]);
  const [categories, setCategories] = useState([]);
  const [year, setYear] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await getTimeline(year, category);
      setEvents(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getTimelineYears().then((res) => setYears(res.data)).catch(console.error);
    getTimelineCategories().then((res) => setCategories(res.data)).catch(console.error);
  }, []);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, category]);

  const selectStyle = {
    padding: "8px",
    borderRadius: "6px",
    background: "#2f3136",
    color: "white",
    border: "1px solid #555",
  };

  return (
    <div style={{ padding: "30px", width: "100%", overflowY: "auto" }}>
      <h1 style={{ marginBottom: "10px" }}>📅 Timeline</h1>
      <p style={{ color: "#aaa", marginBottom: "20px" }}>
        Everything that's happened, in order: conversations, documents, and what your
        AI Twin has learned about you.
      </p>

      <div style={{ display: "flex", gap: "12px", marginBottom: "25px" }}>
        <select value={year} onChange={(e) => setYear(e.target.value)} style={selectStyle}>
          <option value="">All years</option>
          {years.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>

        <select value={category} onChange={(e) => setCategory(e.target.value)} style={selectStyle}>
          <option value="">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c.replace("_", " ")}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <p style={{ color: "#888" }}>Loading...</p>
      ) : events.length === 0 ? (
        <h3>No events found.</h3>
      ) : (
        <div style={{ position: "relative", paddingLeft: "20px" }}>
          <div
            style={{
              position: "absolute", left: "8px", top: 0, bottom: 0,
              width: "2px", background: "#444",
            }}
          />

          {events.map((event, i) => (
            <div key={i} style={{ position: "relative", marginBottom: "20px", paddingLeft: "25px" }}>
              <div
                style={{
                  position: "absolute", left: "-21px", top: "4px",
                  width: "14px", height: "14px", borderRadius: "50%",
                  background: CATEGORY_COLORS[event.category] || "#495057",
                  border: "2px solid #2f3136",
                }}
              />

              <div
                style={{
                  background: "#40414f", color: "white",
                  padding: "14px 18px", borderRadius: "10px",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: 600 }}>
                    {TYPE_ICONS[event.type] || "•"} {event.title}
                  </span>
                  <span style={{ color: "#999", fontSize: "12px", whiteSpace: "nowrap", marginLeft: "12px" }}>
                    {event.date}
                  </span>
                </div>

                <div style={{ marginTop: "6px" }}>
                  <span
                    style={{
                      background: CATEGORY_COLORS[event.category] || "#495057",
                      color: "white", borderRadius: "999px", padding: "2px 10px",
                      fontSize: "11px", textTransform: "capitalize",
                    }}
                  >
                    {event.category?.replace("_", " ")}
                  </span>
                  {event.confidence != null && (
                    <span style={{ marginLeft: "10px", color: "#999", fontSize: "11px" }}>
                      {Math.round(event.confidence * 100)}% confidence
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default TimelinePanel;
