import {
  useEffect,
  useState,
  useImperativeHandle,
  forwardRef,
} from "react";

import {
  getConversations,
  searchConversations,
  createConversation,
  renameConversation,
  deleteConversation,
} from "../services/api";

const Sidebar = forwardRef(
  ({ onSelectConversation, onShowMemories }, ref) => {

    const [conversations, setConversations] = useState([]);

    const [editingId, setEditingId] = useState(null);
    const [editingTitle, setEditingTitle] = useState("");

    const [deletingId, setDeletingId] = useState(null);

    // Search
    const [searchQuery, setSearchQuery] = useState("");
    const [searching, setSearching] = useState(false);

    // -----------------------------------
    // Load all conversations
    // -----------------------------------

    const loadConversations = async () => {
      try {
        const response = await getConversations();
        setConversations(response.data);
      } catch (err) {
        console.error(
          "Failed to load conversations:",
          err
        );
      }
    };

    // -----------------------------------
    // Search conversations
    // -----------------------------------

    const handleSearch = async (value) => {

      setSearchQuery(value);

      const query = value.trim();

      if (!query) {
        setSearching(false);
        await loadConversations();
        return;
      }

      try {

        setSearching(true);

        const response =
          await searchConversations(query);

        setConversations(response.data);

      } catch (err) {

        console.error(
          "Failed to search conversations:",
          err
        );

      } finally {

        setSearching(false);

      }
    };

    // -----------------------------------
    // Initial load
    // -----------------------------------

    useEffect(() => {
      loadConversations();
    }, []);

    // -----------------------------------
    // Allow parent to refresh sidebar
    // -----------------------------------

    useImperativeHandle(ref, () => ({
      refresh: loadConversations,
    }));

    // -----------------------------------
    // New Chat
    // -----------------------------------

    const newChat = async () => {

      try {

        const response =
          await createConversation("New Chat");

        setSearchQuery("");

        await loadConversations();

        onSelectConversation(
          response.data.id
        );

      } catch (err) {

        console.error(
          "Failed to create conversation:",
          err
        );

      }
    };

    // -----------------------------------
    // Start Rename
    // -----------------------------------

    const startRename = (chat) => {

      setEditingId(chat.id);
      setEditingTitle(chat.title);

    };

    // -----------------------------------
    // Save Rename
    // -----------------------------------

    const saveRename = async (id) => {

      const title =
        editingTitle.trim();

      if (!title) {

        alert(
          "Conversation title cannot be empty."
        );

        return;
      }

      try {

        await renameConversation(
          id,
          title
        );

        setEditingId(null);
        setEditingTitle("");

        if (searchQuery.trim()) {

          const response =
            await searchConversations(
              searchQuery.trim()
            );

          setConversations(
            response.data
          );

        } else {

          await loadConversations();

        }

      } catch (err) {

        console.error(
          "Failed to rename conversation:",
          err
        );

        alert(
          "Failed to rename conversation."
        );

      }
    };

    // -----------------------------------
    // Cancel Rename
    // -----------------------------------

    const cancelRename = () => {

      setEditingId(null);
      setEditingTitle("");

    };

    // -----------------------------------
    // Delete Conversation
    // -----------------------------------

    const handleDelete = async (chat) => {

      const confirmed =
        window.confirm(
          `Delete "${chat.title}"?\n\n` +
          "This will permanently delete the conversation, " +
          "messages, attachments, and uploaded files."
        );

      if (!confirmed) {
        return;
      }

      try {

        setDeletingId(chat.id);

        await deleteConversation(
          chat.id
        );

        if (searchQuery.trim()) {

          const response =
            await searchConversations(
              searchQuery.trim()
            );

          setConversations(
            response.data
          );

        } else {

          await loadConversations();

        }

        setDeletingId(null);

      } catch (err) {

        console.error(
          "Failed to delete conversation:",
          err
        );

        setDeletingId(null);

        alert(
          "Failed to delete conversation."
        );

      }
    };

    // -----------------------------------
    // Highlight searched text
    // -----------------------------------

    const renderMatch = (text) => {

      if (!text) {
        return null;
      }

      const query =
        searchQuery.trim();

      if (!query) {
        return text;
      }

      const index =
        text.toLowerCase().indexOf(
          query.toLowerCase()
        );

      if (index === -1) {

        return text.length > 120
          ? `${text.substring(0, 120)}...`
          : text;

      }

      const start =
        Math.max(0, index - 50);

      const end =
        Math.min(
          text.length,
          index + query.length + 70
        );

      let preview =
        text.substring(start, end);

      if (start > 0) {
        preview = `...${preview}`;
      }

      if (end < text.length) {
        preview = `${preview}...`;
      }

      return preview;
    };

    return (
      <div className="sidebar">

        {/* ================================= */}
        {/* HEADER */}
        {/* ================================= */}

        <h2>AI Twin</h2>

        {/* ================================= */}
        {/* NEW CHAT */}
        {/* ================================= */}

        <button
          className="new-chat"
          onClick={newChat}
        >
          + New Chat
        </button>

        {/* ================================= */}
        {/* MEMORIES */}
        {/* ================================= */}

        <button
          className="new-chat"
          onClick={onShowMemories}
          style={{
            marginTop: "10px",
          }}
        >
          🧠 Memories
        </button>

        {/* ================================= */}
        {/* CONVERSATION SEARCH */}
        {/* ================================= */}

        <div className="conversation-search">

          <input
            type="text"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={(e) =>
              handleSearch(e.target.value)
            }
          />

          {searchQuery && (
            <button
              type="button"
              className="clear-search"
              onClick={() =>
                handleSearch("")
              }
              title="Clear search"
            >
              ×
            </button>
          )}

        </div>

        {/* ================================= */}
        {/* SEARCH STATUS */}
        {/* ================================= */}

        {searchQuery.trim() && (
          <div className="search-status">

            {searching
              ? "Searching..."
              : `${conversations.length} conversation${
                  conversations.length === 1
                    ? ""
                    : "s"
                } found`}

          </div>
        )}

        {/* ================================= */}
        {/* CONVERSATION LIST */}
        {/* ================================= */}

        <div className="conversation-list">

          {conversations.length === 0 &&
          !searching ? (

            <div className="no-conversations">
              {searchQuery.trim()
                ? "No matching conversations"
                : "No conversations yet"}
            </div>

          ) : (

            conversations.map((chat) => (

              <div
                key={chat.id}
                className="conversation"
              >

                {/* ================================= */}
                {/* NORMAL MODE */}
                {/* ================================= */}

                {editingId !== chat.id ? (

                  <>

                    <div
                      className="conversation-main"
                      onClick={() =>
                        onSelectConversation(
                          chat.id
                        )
                      }
                    >

                      {/* Conversation title */}

                      <div className="conversation-title">
                        💬 {chat.title}
                      </div>

                      {/* Matching message */}

                      {searchQuery.trim() &&
                        chat.match && (

                          <div className="conversation-match">

                            <span className="match-label">
                              Message:
                            </span>

                            {renderMatch(
                              chat.match
                            )}

                          </div>

                        )}

                    </div>

                    {/* ================================= */}
                    {/* ACTION BUTTONS */}
                    {/* ================================= */}

                    <div className="conversation-actions">

                      <button
                        type="button"
                        onClick={(e) => {

                          e.stopPropagation();

                          startRename(chat);

                        }}
                        title="Rename conversation"
                        disabled={
                          deletingId ===
                          chat.id
                        }
                      >
                        ✏️
                      </button>

                      <button
                        type="button"
                        onClick={(e) => {

                          e.stopPropagation();

                          handleDelete(chat);

                        }}
                        title="Delete conversation"
                        disabled={
                          deletingId ===
                          chat.id
                        }
                      >
                        {deletingId === chat.id
                          ? "..."
                          : "🗑️"}
                      </button>

                    </div>

                  </>

                ) : (

                  /* ================================= */
                  /* RENAME MODE */
                  /* ================================= */

                  <div className="conversation-edit">

                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) =>
                        setEditingTitle(
                          e.target.value
                        )
                      }
                      onKeyDown={(e) => {

                        if (
                          e.key === "Enter"
                        ) {
                          saveRename(
                            chat.id
                          );
                        }

                        if (
                          e.key === "Escape"
                        ) {
                          cancelRename();
                        }

                      }}
                      autoFocus
                    />

                    <div className="conversation-edit-actions">

                      <button
                        type="button"
                        onClick={() =>
                          saveRename(
                            chat.id
                          )
                        }
                        title="Save"
                      >
                        ✓
                      </button>

                      <button
                        type="button"
                        onClick={
                          cancelRename
                        }
                        title="Cancel"
                      >
                        ×
                      </button>

                    </div>

                  </div>

                )}

              </div>

            ))

          )}

        </div>

      </div>
    );
  }
);

export default Sidebar;