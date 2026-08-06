import { useEffect, useState } from "react";
import {
  getMemories,
  deleteMemory,
  updateMemory,
  searchMemories,
} from "../services/api";

function MemoryPanel() {
  const [memories, setMemories] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [editedMemory, setEditedMemory] = useState("");
  const [editedImportance, setEditedImportance] = useState(5);
  const [search, setSearch] = useState("");

  const loadMemories = async () => {
    try {
      const res = await getMemories();
      setMemories(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadMemories();
  }, []);

  const deleteMemoryHandler = async (id) => {
    try {
      await deleteMemory(id);
      loadMemories();
    } catch (err) {
      console.error(err);
      alert("Failed to delete memory.");
    }
  };

  const startEditing = (memory) => {
    setEditingId(memory.id);
    setEditedMemory(memory.memory);
    setEditedImportance(memory.importance);
  };

  const saveEdit = async () => {
    try {
      await updateMemory(
        editingId,
        editedMemory,
        Number(editedImportance)
      );

      setEditingId(null);
      loadMemories();
    } catch (err) {
      console.error(err);
      alert("Failed to update memory.");
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
  };

  return (
    <div
      style={{
        padding: "30px",
        width: "100%",
        overflowY: "auto",
      }}
    >
      <h1 style={{ marginBottom: "25px" }}>
        🧠 Long-Term Memories
      </h1>
      <input
        type="text"
        placeholder="🔍 Search memories..."
        value={search}
       onChange={async (e) => {
  const value = e.target.value;

  setSearch(value);

  if (value.trim() === "") {
    loadMemories();
    return;
  }

  try {
    const res = await searchMemories(value);

    setMemories(
      res.data.map((text, index) => ({
        id: index,
        memory: text,
        importance: "-",
      }))
    );
  } catch (err) {
    console.error(err);
  }
}}
        style={{
           width: "100%",
            padding: "12px",
            marginBottom: "20px",
           borderRadius: "8px",
            border: "1px solid #555",
            background: "#2f3136",
           color: "white",
          fontSize: "16px",
        }}
     />

      {memories.length === 0 ? (
        <h3>No memories found.</h3>
      ) : (
        memories
  
  .map((memory) => (
          <div
            key={memory.id}
            style={{
              background: "#40414f",
              color: "white",
              padding: "20px",
              marginBottom: "15px",
              borderRadius: "10px",
            }}
          >
            {editingId === memory.id ? (
              <>
                <input
                  type="text"
                  value={editedMemory}
                  onChange={(e) =>
                    setEditedMemory(e.target.value)
                  }
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
                  onChange={(e) =>
                    setEditedImportance(e.target.value)
                  }
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
                    background: "#28a745",
                    color: "white",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    cursor: "pointer",
                    marginRight: "10px",
                  }}
                >
                  💾 Save
                </button>

                <button
                  onClick={cancelEdit}
                  style={{
                    background: "#6c757d",
                    color: "white",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
              </>
            ) : (
              <>
                <h3>{memory.memory}</h3>

                <p>
                  Importance: {memory.importance}
                </p>

                <button
                  onClick={() => startEditing(memory)}
                  style={{
                    background: "#007bff",
                    color: "white",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    cursor: "pointer",
                    marginRight: "10px",
                  }}
                >
                  ✏ Edit
                </button>

                <button
                  onClick={() =>
                    deleteMemoryHandler(memory.id)
                  }
                  style={{
                    background: "#dc3545",
                    color: "white",
                    border: "none",
                    padding: "8px 16px",
                    borderRadius: "6px",
                    cursor: "pointer",
                  }}
                >
                  🗑 Delete
                </button>
              </>
            )}
          </div>
        ))
      )}
    </div>
  );
}

export default MemoryPanel;