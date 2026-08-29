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

        messages.map(
          (message, index) => (

            <Message
              key={
                message.id ||
                index
              }

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