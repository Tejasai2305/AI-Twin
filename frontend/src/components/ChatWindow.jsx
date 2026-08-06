import { useEffect, useRef } from "react";
import Message from "./Message";

function ChatWindow({ messages }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div
          style={{
            color: "#b5b5b5",
            textAlign: "center",
            marginTop: "120px",
            fontSize: "22px",
          }}
        >
          Start a conversation...
        </div>
      ) : (
        messages.map((message, index) => (
          <Message
            key={index}
            role={message.role}
            content={message.content}
          />
        ))
      )}

      <div ref={bottomRef} />
    </div>
  );
}

export default ChatWindow;