import {
  useEffect,
  useRef,
} from "react";

import Message from "./Message";


function ChatWindow({
  messages,
  onRegenerate,
  onEdit,
  editingMessageId,
  regeneratingMessageId,
  isStreaming,
}) {

  const bottomRef =
    useRef(null);


  useEffect(() => {

    bottomRef.current?.scrollIntoView({
      behavior: "auto",
      block: "end",
    });

  }, [messages]);


  return (
    <div className="chat-window">

      {messages.length === 0 ? (

        <div className="ai-twin-empty">
  <div className={`ai-twin-core ${isStreaming ? "twin-thinking" : ""}`}>
    <div className="ai-twin-core-ring ring-one"></div>
    <div className="ai-twin-core-ring ring-two"></div>
    <div className="ai-twin-core-ring ring-three"></div>
    <div className="ai-twin-core-center">
      <span>AI</span>
      <span>TWIN</span>
    </div>
  </div>

  <div className="ai-twin-status">
    <span className="status-dot"></span>
    AI TWIN ONLINE
  </div>

  <h1>Your personal AI intelligence layer</h1>

  <p>
    Memory, knowledge, insights and decisions • connected in one place.
  </p>

  <div className="ai-twin-capabilities">
  <div className="ai-twin-card">
    <div className="ai-twin-card-icon">M</div><div><strong>Memory</strong>
      <span>Remembers what matters</span>
    </div>
  </div>

  <div className="ai-twin-card">
    <div className="ai-twin-card-icon">K</div><div><strong>Knowledge</strong>
      <span>Connects your information</span>
    </div>
  </div>

  <div className="ai-twin-card">
    <div className="ai-twin-card-icon">D</div><div><strong>Decision Intelligence</strong>
      <span>Helps structure your choices</span>
    </div>
  </div>
</div>
</div>

      ) : (

        messages.map(
          (message, index) => (

            <Message
              key={`${message.id || "message"}-${index}`}

              id={
                message.id
              }

              role={
                message.role
              }

              content={
                message.content
              }

              attachments={
                message.attachments ||
                []
              }

              onRegenerate={
                onRegenerate
              }

              onEdit={
                onEdit
              }

              isEditing={
                editingMessageId ===
                message.id
              }

              isRegenerating={
                regeneratingMessageId ===
                message.id
              }
            />

          )
        )

      )}

      <div
        ref={bottomRef}
      />

    </div>
  );
}


export default ChatWindow;








