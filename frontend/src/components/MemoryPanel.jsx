import { useEffect, useState } from "react";
import {
  getMemoriesDetailed,
  getMemoryTypes,
  getContradictions,
  getMemoryTimeline,
  deactivateMemory,
  reactivateMemory,
  updateMemory,
  searchMemories,
} from "../services/api";

const TYPE_COLORS = {
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
  other: "#495057",
};

function TypeBadge({ type }) {
  const color = TYPE_COLORS[type] || "#495057";
  return (
    <span
      style={{
        background: color,
        color: "white",
        borderRadius: "999px",
        padding: "3px 10px",
        fontSize: "12px",
        marginRight: "8px",
        textTransform: "capitalize",
      }}
    >
      {type?.replace("_", " ") || "other"}
    </span>
  );
}

function ConfidenceBadge({ confidence }) {
  const value = typeof confidence === "number" ? confidence : 0.7;
  const pct = Math.round(value * 100);
  const color = value >= 0.8 ? "#28a745" : value >= 0.5 ? "#ffc107" : "#dc3545";
  return (
    <span
      style={{
        color,
        fontSize: "12px",
        fontWeight: 600,
        marginRight: "8px",
      }}
      title="Confidence: how explicitly this was stated"
    >
      {pct}% confidence
    </span>
  );
}

function MemoryPanel() {
  const [tab, setTab] = useState("memories"); // "memories" | "contradictions"

  const [memories, setMemories] = useState([]);
  const [types, setTypes] = useState([]);
  const [typeFilter, setTypeFilter] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);

  const [contradictions, setContradictions] = useState([]);

  const [editingId, setEditingId] = useState(null);
  const [editedMemory, setEditedMemory] = useState("");
  const [editedImportance, setEditedImportance] = useState(5);

  const [search, setSearch] = useState("");
  const [searching, setSearching] = useState(false);

  const [timelineFor, setTimelineFor] = useState(null); // memory id
  const [timeline, setTimeline] = useState([]);

  const loadMemories = async () => {
    try {
      const res = await getMemoriesDetailed(typeFilter, includeInactive);
      setMemories(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadTypes = async () => {
    try {
      const res = await getMemoryTypes();
      setTypes(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadContradictions = async () => {
    try {
      const res = await getContradictions();
      setContradictions(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadTypes();
  }, []);

  useEffect(() => {
    if (tab === "memories") {
      loadMemories();
    } else {
      loadContradictions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, typeFilter, includeInactive]);

  const handleSearch = async (value) => {
    setSearch(value);

    if (value.trim() === "") {
      setSearching(false);
      loadMemories();
      return;
    }

    setSearching(true);

    try {
      const res = await searchMemories(value);

      setMemories(
        res.data.map((text, index) => ({
          id: `search-${index}`,
          memory: text,
          importance: "-",
          memory_type: null,
          confidence: null,
          source: null,
          is_active: true,
        }))
      );
    } catch (err) {
      console.error(err);
    }
  };

  const deactivateHandler = async (id) => {
    try {
      await deactivateMemory(id);
      loadMemories();
    } catch (err) {
      console.error(err);
      alert("Failed to deactivate memory.");
    }
  };

  const reactivateHandler = async (id) => {
    try {
      await reactivateMemory(id);
      loadMemories();
    } catch (err) {
      console.error(err);
      alert("Failed to reactivate memory.");
    }
  };

  const startEditing = (memory) => {
    setEditingId(memory.id);
    setEditedMemory(memory.memory);
    setEditedImportance(memory.importance);
  };

  const saveEdit = async () => {
    try {
      await updateMemory(editingId, editedMemory, Number(editedImportance));
      setEditingId(null);
      loadMemories();
    } catch (err) {
      console.error(err);
      alert("Failed to update memory.");
    }
  };

  const cancelEdit = () => setEditingId(null);

  const openTimeline = async (id) => {
    try {
      const res = await getMemoryTimeline(id);
      setTimeline(res.data);
      setTimelineFor(id);
    } catch (err) {
      console.error(err);
      alert("Failed to load timeline.");
    }
  };

  const tabButtonStyle = (active) => ({
    background: active ? "#40414f" : "transparent",
    color: "white",
    border: "1px solid #555",
    padding: "8px 18px",
    borderRadius: "8px",
    cursor: "pointer",
    marginRight: "10px",
    fontWeight: active ? 600 : 400,
  });

  return (
    <div style={{ padding: "30px", width: "100%", overflowY: "auto" }}>
      <h1 style={{ marginBottom: "10px" }}>🧠 Memory Center</h1>
      <p style={{ color: "#aaa", marginBottom: "20px" }}>
        Everything your AI Twin has learned about you, where it came from, and
        how confident it is.
      </p>

      <div style={{ marginBottom: "20px" }}>
        <button style={tabButtonStyle(tab === "memories")} onClick={() => setTab("memories")}>
          All Memories
        </button>
        <button
          style={tabButtonStyle(tab === "contradictions")}
          onClick={() => setTab("contradictions")}
        >
          Contradictions {contradictions.length > 0 ? `(${contradictions.length})` : ""}
        </button>
      </div>

      {tab === "memories" && (
        <>
          <input
            type="text"
            placeholder="🔍 Search memories..."
            value={search}
            onChange={(e) => handleSearch(e.target.value)}
            style={{
              width: "100%",
              padding: "12px",
              marginBottom: "15px",
              borderRadius: "8px",
              border: "1px solid #555",
              background: "#2f3136",
              color: "white",
              fontSize: "16px",
            }}
          />

          {!searching && (
            <div style={{ display: "flex", gap: "12px", marginBottom: "20px", alignItems: "center" }}>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                style={{
                  padding: "8px",
                  borderRadius: "6px",
                  background: "#2f3136",
                  color: "white",
                  border: "1px solid #555",
                }}
              >
                <option value="">All types</option>
                {types.map((t) => (
                  <option key={t} value={t}>
                    {t.replace("_", " ")}
                  </option>
                ))}
              </select>

              <label style={{ color: "#ccc", fontSize: "14px" }}>
                <input
                  type="checkbox"
                  checked={includeInactive}
                  onChange={(e) => setIncludeInactive(e.target.checked)}
                  style={{ marginRight: "6px" }}
                />
                Show deactivated / superseded memories
              </label>
            </div>
          )}

          {memories.length === 0 ? (
            <h3>No memories found.</h3>
          ) : (
            memories.map((memory) => (
              <div
                key={memory.id}
                style={{
                  background: memory.is_active === false ? "#33343d" : "#40414f",
                  color: "white",
                  padding: "20px",
                  marginBottom: "15px",
                  borderRadius: "10px",
                  opacity: memory.is_active === false ? 0.7 : 1,
                }}
              >
                {editingId === memory.id ? (
                  <>
                    <input
                      type="text"
                      value={editedMemory}
                      onChange={(e) => setEditedMemory(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "10px",
                        marginBottom: "10px",
                        borderRadius: "6px",
                        border: "none",
                      }}
                    />
                    <input
                      type="number"
                      value={editedImportance}
                      onChange={(e) => setEditedImportance(e.target.value)}
                      style={{
                        width: "100px",
                        padding: "8px",
                        marginBottom: "15px",
                        borderRadius: "6px",
                        border: "none",
                        display: "block",
                      }}
                    />
                    <button
                      onClick={saveEdit}
                      style={{
                        background: "#28a745", color: "white", border: "none",
                        padding: "8px 16px", borderRadius: "6px", cursor: "pointer", marginRight: "10px",
                      }}
                    >
                      💾 Save
                    </button>
                    <button
                      onClick={cancelEdit}
                      style={{
                        background: "#6c757d", color: "white", border: "none",
                        padding: "8px 16px", borderRadius: "6px", cursor: "pointer",
                      }}
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <div style={{ marginBottom: "8px" }}>
                      {memory.memory_type && <TypeBadge type={memory.memory_type} />}
                      {memory.confidence != null && <ConfidenceBadge confidence={memory.confidence} />}
                      {memory.is_active === false && (
                        <span style={{ color: "#dc3545", fontSize: "12px", fontWeight: 600 }}>
                          superseded / inactive
                        </span>
                      )}
                    </div>

                    <h3 style={{ margin: "0 0 6px 0" }}>{memory.memory}</h3>

                    <p style={{ margin: "0 0 6px 0", color: "#bbb", fontSize: "13px" }}>
                      Importance: {memory.importance}
                      {memory.source && <> · Source: {memory.source}</>}
                    </p>

                    {memory.evidence && (
                      <p style={{ margin: "0 0 10px 0", color: "#999", fontSize: "12px", fontStyle: "italic" }}>
                        "{memory.evidence}"
                      </p>
                    )}

                    <div>
                      {!searching && (
                        <>
                          <button
                            onClick={() => startEditing(memory)}
                            style={{
                              background: "#007bff", color: "white", border: "none",
                              padding: "8px 16px", borderRadius: "6px", cursor: "pointer", marginRight: "10px",
                            }}
                          >
                            ✏ Edit
                          </button>

                          <button
                            onClick={() => openTimeline(memory.id)}
                            style={{
                              background: "#6610f2", color: "white", border: "none",
                              padding: "8px 16px", borderRadius: "6px", cursor: "pointer", marginRight: "10px",
                            }}
                          >
                            🕓 Timeline
                          </button>

                          {memory.is_active === false ? (
                            <button
                              onClick={() => reactivateHandler(memory.id)}
                              style={{
                                background: "#28a745", color: "white", border: "none",
                                padding: "8px 16px", borderRadius: "6px", cursor: "pointer",
                              }}
                            >
                              ♻ Reactivate
                            </button>
                          ) : (
                            <button
                              onClick={() => deactivateHandler(memory.id)}
                              style={{
                                background: "#dc3545", color: "white", border: "none",
                                padding: "8px 16px", borderRadius: "6px", cursor: "pointer",
                              }}
                            >
                              🗑 Deactivate
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))
          )}
        </>
      )}

      {tab === "contradictions" && (
        <>
          {contradictions.length === 0 ? (
            <h3>No contradictions detected yet.</h3>
          ) : (
            contradictions.map((c) => (
              <div
                key={c.history_id}
                style={{
                  background: "#40414f",
                  color: "white",
                  padding: "20px",
                  marginBottom: "15px",
                  borderRadius: "10px",
                }}
              >
                {c.memory_type && <TypeBadge type={c.memory_type} />}
                {c.confidence != null && <ConfidenceBadge confidence={c.confidence} />}

                <p style={{ margin: "10px 0 4px 0", color: "#dc3545", textDecoration: "line-through" }}>
                  {c.previous_value}
                </p>
                <p style={{ margin: "0 0 8px 0", color: "#28a745", fontWeight: 600 }}>
                  → {c.current_value}
                </p>
                <p style={{ margin: 0, color: "#888", fontSize: "12px" }}>
                  Resolved {c.changed_at}
                </p>

                <button
                  onClick={() => openTimeline(c.memory_id)}
                  style={{
                    marginTop: "10px",
                    background: "#6610f2", color: "white", border: "none",
                    padding: "8px 16px", borderRadius: "6px", cursor: "pointer",
                  }}
                >
                  🕓 View full timeline
                </button>
              </div>
            ))
          )}
        </>
      )}

      {timelineFor !== null && (
        <div
          onClick={() => setTimelineFor(null)}
          style={{
            position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
            background: "rgba(0,0,0,0.6)", display: "flex",
            alignItems: "center", justifyContent: "center", zIndex: 1000,
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#2f3136", color: "white", padding: "25px",
              borderRadius: "10px", maxWidth: "600px", width: "90%",
              maxHeight: "80vh", overflowY: "auto",
            }}
          >
            <h2 style={{ marginTop: 0 }}>Timeline</h2>

            {timeline.map((entry, i) => (
              <div
                key={entry.id}
                style={{
                  borderLeft: "3px solid " + (entry.is_active ? "#28a745" : "#555"),
                  paddingLeft: "15px",
                  marginBottom: "15px",
                }}
              >
                <p style={{ margin: "0 0 4px 0", fontWeight: entry.is_active ? 700 : 400 }}>
                  {entry.memory} {entry.is_active && "(current)"}
                </p>
                <p style={{ margin: 0, color: "#999", fontSize: "12px" }}>
                  Valid {entry.valid_from} {entry.valid_until ? `→ ${entry.valid_until}` : "→ present"}
                </p>
                {i < timeline.length - 1 && (
                  <p style={{ margin: "4px 0 0 0", color: "#666" }}>↓ superseded by</p>
                )}
              </div>
            ))}

            <button
              onClick={() => setTimelineFor(null)}
              style={{
                background: "#6c757d", color: "white", border: "none",
                padding: "8px 16px", borderRadius: "6px", cursor: "pointer", marginTop: "10px",
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default MemoryPanel;
