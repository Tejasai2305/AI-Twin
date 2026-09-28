import { useEffect, useMemo, useState } from "react";
import { getGraph, getGraphNode } from "../services/graphApi";

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

const WIDTH = 900;
const HEIGHT = 700;
const CENTER = { x: WIDTH / 2, y: HEIGHT / 2 };
const CATEGORY_RADIUS = 220;
const FACT_RADIUS = 110;

function layoutGraph(graph) {
  const categoryNodes = graph.nodes.filter((n) => n.type === "category");
  const factNodes = graph.nodes.filter((n) => n.type === "fact");

  const positions = {
    user: { ...CENTER },
  };

  categoryNodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / Math.max(categoryNodes.length, 1) - Math.PI / 2;
    positions[node.id] = {
      x: CENTER.x + CATEGORY_RADIUS * Math.cos(angle),
      y: CENTER.y + CATEGORY_RADIUS * Math.sin(angle),
    };
  });

  categoryNodes.forEach((catNode) => {
    const facts = factNodes.filter((f) => f.category === catNode.category);
    const catPos = positions[catNode.id];

    // Direction pointing away from the user, so satellite facts fan
    // outward instead of back toward the center.
    const baseAngle = Math.atan2(catPos.y - CENTER.y, catPos.x - CENTER.x);

    facts.forEach((fact, i) => {
      const spread = Math.min(facts.length, 6);
      const offset = (i - (facts.length - 1) / 2) * (Math.PI / 5);
      const angle = baseAngle + (spread > 1 ? offset : 0);

      positions[fact.id] = {
        x: catPos.x + FACT_RADIUS * Math.cos(angle),
        y: catPos.y + FACT_RADIUS * Math.sin(angle),
      };
    });
  });

  return positions;
}

function truncate(text, max = 28) {
  if (!text) return "";
  return text.length > max ? text.slice(0, max - 1) + "…" : text;
}

function KnowledgeGraphPanel() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [includeInactive, setIncludeInactive] = useState(false);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await getGraph(includeInactive);
      setGraph(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [includeInactive]);

  const positions = useMemo(() => layoutGraph(graph), [graph]);

  const handleNodeClick = async (node) => {
    try {
      const res = await getGraphNode(node.id);
      setSelected(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div style={{ padding: "30px", color: "white" }}>Loading knowledge graph…</div>;
  }

  return (
    <div style={{ padding: "30px", width: "100%", overflow: "auto", color: "white" }}>
      <h1 style={{ marginBottom: "10px" }}>🕸️ Knowledge Graph</h1>
      <p style={{ color: "#aaa", marginBottom: "10px" }}>
        How your stored facts connect to you, grouped by category. Click any node for details.
      </p>

      <label style={{ color: "#ccc", fontSize: "14px", display: "block", marginBottom: "15px" }}>
        <input
          type="checkbox"
          checked={includeInactive}
          onChange={(e) => setIncludeInactive(e.target.checked)}
          style={{ marginRight: "6px" }}
        />
        Include superseded / inactive facts
      </label>

      <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
        <svg
          width={WIDTH}
          height={HEIGHT}
          style={{ background: "#2f3136", borderRadius: "12px", flexShrink: 0 }}
        >
          {graph.edges.map((edge) => {
            const from = positions[edge.source];
            const to = positions[edge.target];
            if (!from || !to) return null;
            return (
              <line
                key={edge.id}
                x1={from.x}
                y1={from.y}
                x2={to.x}
                y2={to.y}
                stroke={edge.is_active ? "#666" : "#444"}
                strokeWidth={edge.is_active ? 1.5 : 1}
                strokeDasharray={edge.is_active ? "0" : "4 3"}
              />
            );
          })}

          {graph.nodes.map((node) => {
            const pos = positions[node.id];
            if (!pos) return null;

            const isUser = node.type === "user";
            const isCategory = node.type === "category";
            const radius = isUser ? 34 : isCategory ? 22 : 14;
            const color = isUser
              ? "#ffffff"
              : TYPE_COLORS[node.category] || "#888";

            return (
              <g
                key={node.id}
                transform={`translate(${pos.x}, ${pos.y})`}
                style={{ cursor: "pointer" }}
                onClick={() => handleNodeClick(node)}
                opacity={node.is_active === false ? 0.45 : 1}
              >
                <circle
                  r={radius}
                  fill={isUser ? "#1f2023" : color}
                  stroke={isUser ? "#fff" : "#222"}
                  strokeWidth={isUser ? 2 : 1}
                />
                <text
                  y={radius + 14}
                  textAnchor="middle"
                  fontSize={isCategory ? 12 : 10}
                  fontWeight={isUser || isCategory ? 700 : 400}
                  fill="white"
                >
                  {isUser ? "You" : truncate(node.label, isCategory ? 20 : 24)}
                </text>
              </g>
            );
          })}
        </svg>

        <div style={{ minWidth: "260px", flex: 1 }}>
          {selected ? (
            <div style={{ background: "#40414f", padding: "20px", borderRadius: "10px" }}>
              {selected.type === "fact" ? (
                <>
                  <span
                    style={{
                      background: TYPE_COLORS[selected.memory.memory_type] || "#495057",
                      color: "white",
                      borderRadius: "999px",
                      padding: "3px 10px",
                      fontSize: "12px",
                      textTransform: "capitalize",
                    }}
                  >
                    {selected.memory.memory_type?.replace("_", " ")}
                  </span>
                  <h3 style={{ margin: "12px 0 6px 0" }}>{selected.memory.memory}</h3>
                  <p style={{ margin: "0 0 4px 0", color: "#bbb", fontSize: "13px" }}>
                    Confidence: {Math.round((selected.memory.confidence || 0) * 100)}% ·
                    Source: {selected.memory.source}
                  </p>
                  {selected.memory.evidence && (
                    <p style={{ color: "#999", fontSize: "12px", fontStyle: "italic" }}>
                      "{selected.memory.evidence}"
                    </p>
                  )}
                  {selected.timeline.length > 1 && (
                    <div style={{ marginTop: "12px" }}>
                      <strong style={{ fontSize: "13px" }}>Timeline:</strong>
                      {selected.timeline.map((t) => (
                        <p key={t.id} style={{ fontSize: "12px", color: t.is_active ? "#28a745" : "#888", margin: "4px 0" }}>
                          {t.memory} {t.is_active ? "(current)" : "(past)"}
                        </p>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <h3 style={{ margin: 0 }}>{selected.label}</h3>
              )}
            </div>
          ) : (
            <div style={{ color: "#888", padding: "20px" }}>
              Click a node in the graph to see its details here.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default KnowledgeGraphPanel;
