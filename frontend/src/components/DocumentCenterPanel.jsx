import { useEffect, useState } from "react";
import { getDocuments, deleteDocument } from "../services/documentsApi";

function DocumentCenterPanel() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await getDocuments();
      setDocuments(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id, filename) => {
    if (!window.confirm(`Delete "${filename}"? This removes it and everything it taught your AI Twin's document search.`)) {
      return;
    }
    try {
      await deleteDocument(id);
      load();
    } catch (err) {
      console.error(err);
      alert("Failed to delete document.");
    }
  };

  return (
    <div style={{ padding: "30px", width: "100%", overflowY: "auto" }}>
      <h1 style={{ marginBottom: "6px" }}>📄 Document Center</h1>
      <p style={{ color: "#aaa", marginBottom: "20px" }}>
        Every document uploaded across your conversations, and its indexing status.
        Upload new PDFs from within a chat.
      </p>

      {loading ? (
        <p style={{ color: "#888" }}>Loading...</p>
      ) : documents.length === 0 ? (
        <h3>No documents uploaded yet.</h3>
      ) : (
        documents.map((doc) => (
          <div
            key={doc.id}
            style={{
              background: "#40414f",
              color: "white",
              padding: "18px 20px",
              marginBottom: "14px",
              borderRadius: "10px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <h3 style={{ margin: "0 0 6px 0" }}>📄 {doc.filename}</h3>
              <p style={{ margin: 0, color: "#aaa", fontSize: "13px" }}>
                Uploaded {doc.created_at} · {doc.chunk_count} indexed chunk
                {doc.chunk_count === 1 ? "" : "s"}
              </p>
              <p style={{ margin: "4px 0 0 0", fontSize: "12px" }}>
                {doc.indexed ? (
                  <span style={{ color: "#28a745" }}>● Indexed and searchable</span>
                ) : (
                  <span style={{ color: "#dc3545" }}>● Not indexed</span>
                )}
                {!doc.file_exists && (
                  <span style={{ color: "#ffc107", marginLeft: "12px" }}>
                    ⚠ File missing on disk
                  </span>
                )}
              </p>
            </div>

            <button
              onClick={() => handleDelete(doc.id, doc.filename)}
              style={{
                background: "#dc3545", color: "white", border: "none",
                padding: "8px 16px", borderRadius: "6px", cursor: "pointer",
                whiteSpace: "nowrap",
              }}
            >
              🗑 Delete
            </button>
          </div>
        ))
      )}
    </div>
  );
}

export default DocumentCenterPanel;
