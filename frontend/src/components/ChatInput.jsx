import { useState } from "react";

function ChatInput({
  onSend,
  isStreaming,
  onStop,
}) {
  const [text, setText] = useState("");

  const handleSend = () => {
    if (!text.trim()) return;

    onSend(text);
    setText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();

      if (isStreaming) {
        onStop();
      } else {
        handleSend();
      }
    }
  };

  return (
    <div className="chat-input">
      <textarea
        value={text}
        placeholder="Ask anything..."
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
      />

      {isStreaming ? (
        <button
          onClick={onStop}
          style={{
            backgroundColor: "#dc2626",
          }}
        >
          Stop
        </button>
      ) : (
        <button onClick={handleSend}>
          Send
        </button>
      )}
    </div>
  );
}

export default ChatInput;