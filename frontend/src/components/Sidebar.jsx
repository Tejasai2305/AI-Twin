import {
  useEffect,
  useState,
  useImperativeHandle,
  forwardRef,
} from "react";

import {
  getConversations,
  createConversation,
} from "../services/api";

const Sidebar = forwardRef(
  ({ onSelectConversation, onShowMemories }, ref) => {

    const [conversations, setConversations] = useState([]);

    useEffect(() => {
      loadConversations();
    }, []);

    const loadConversations = async () => {
      try {
        const response = await getConversations();
        setConversations(response.data);
      } catch (err) {
        console.error("Failed to load conversations:", err);
      }
    };

    useImperativeHandle(ref, () => ({
      refresh: loadConversations,
    }));

    const newChat = async () => {
      try {
        const response = await createConversation("New Chat");

        await loadConversations();

        onSelectConversation(response.data.id);

      } catch (err) {
        console.error("Failed to create conversation:", err);
      }
    };

    return (
      <div className="sidebar">

        <h2>AI Twin</h2>

        <button
          className="new-chat"
          onClick={newChat}
        >
          + New Chat
        </button>

        <button
          className="new-chat"
          onClick={onShowMemories}
          style={{ marginTop: "10px" }}
        >
          🧠 Memories
        </button>

        <div className="conversation-list">

          {conversations.map((chat) => (
            <div
              key={chat.id}
              className="conversation"
              onClick={() => onSelectConversation(chat.id)}
            >
              💬 {chat.title}
            </div>
          ))}

        </div>

      </div>
    );
  }
);

export default Sidebar;