import { useState } from "react";
import { globalSearch } from "../services/searchApi";

function SectionCard({ title, icon, children, count }) {
  return (
    <div style={{ marginBottom: "25px" }}>
      <h3 style={{ marginBottom: "10px" }}>
        {icon} {title} {count > 0 && `(${count})`}
      </h3>
      {children}
    </div>
  );
}

function GlobalSearchPanel({ onOpenConversation }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const runSearch = async (value) => {
    setQuery(value);

    if (!value.trim()) {
      setResults(null);
      return;
    }

    setLoading(true);
    try {
      const res = await globalSearch(value);
      setResults(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const cardStyle = {
    background: "#40414f",
    color: "white",
    padding: "14px 18px",
    marginBottom: "10px",
    borderRadius: "10px",
  };

  return (
    <div style={{ padding: "30px", width: "100%", overflowY: "auto" }}>
      <h1 style={{ marginBottom: "10px" }}>🔍 Global Search</h1>
      <p style={{ color: "#aaa", marginBottom: "20px" }}>
        Search across every conversation, memory, and document at once.
      </p>

      <input
        type="text"
        autoFocus
        placeholder="Search everything..."
        value={query}
        onChange={(e) => runSearch(e.target.value)}
        style={{
          width: "100%",
          padding: "14px",
          marginBottom: "25px",
          borderRadius: "8px",
          border: "1px solid #555",
          background: "#2f3136",
          color: "white",
          fontSize: "16px",
        }}
      />

      {loading && <p style={{ color: "#888" }}>Searching...</p>}

      {results && !loading && (
        <>
          {results.conversations.length === 0 &&
            results.memories.length === 0 &&
            results.documents.length === 0 && (
              <h3>No results for "{results.query}".</h3>
            )}

          {results.conversations.length > 0 && (
            <SectionCard title="Conversations" icon="💬" count={results.conversations.length}>
              {results.conversations.map((c) => (
                <div
                  key={c.conversation_id}
                  style={{ ...cardStyle, cursor: onOpenConversation ? "pointer" : "default" }}
                  onClick={() => onOpenConversation && onOpenConversation(c.conversation_id)}
                >
                  <strong>{c.title}</strong>
                  {c.matched_message && (
                    <p style={{ margin: "6px 0 0 0", color: "#bbb", fontSize: "13px" }}>
                      "...{c.matched_message}..."
                    </p>
                  )}
                  <p style={{ margin: "4px 0 0 0", color: "#777", fontSize: "12px" }}>
                    {c.created_at}
                  </p>
                </div>
              ))}
            </SectionCard>
          )}

          {results.memories.length > 0 && (
            <SectionCard title="Memories" icon="🧠" count={results.memories.length}>
              {results.memories.map((m) => (
                <div key={m.id} style={cardStyle}>
                  <p style={{ margin: 0 }}>{m.memory}</p>
                  <p style={{ margin: "4px 0 0 0", color: "#777", fontSize: "12px" }}>
                    {m.memory_type?.replace("_", " ")} · {Math.round((m.confidence || 0.7) * 100)}% confidence
                  </p>
                </div>
              ))}
            </SectionCard>
          )}

          {results.documents.length > 0 && (
            <SectionCard title="Documents" icon="📄" count={results.documents.length}>
              {results.documents.map((d, i) => (
                <div key={i} style={cardStyle}>
                  <strong>{d.filename}</strong>
                  {d.matched_chunk && (
                    <p style={{ margin: "6px 0 0 0", color: "#bbb", fontSize: "13px" }}>
                      "...{d.matched_chunk}..."
                    </p>
                  )}
                </div>
              ))}
            </SectionCard>
          )}
        </>
      )}
    </div>
  );
}

export default GlobalSearchPanel;
