import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  Prism as SyntaxHighlighter,
} from "react-syntax-highlighter";

import {
  oneDark,
} from "react-syntax-highlighter/dist/esm/styles/prism";


function Message({
  id,
  role,
  content,
  attachments = [],
  onRegenerate,
  onEdit,
  isRegenerating = false,
  isEditing = false,
}) {

  const isUser = role === "user";

  const [editText, setEditText] = useState(
    content || ""
  );

  const [copiedCode, setCopiedCode] = useState("");

  useEffect(() => {

    if (isEditing) {
      setEditText(content || "");
    }

  }, [content, isEditing]);


  // ==========================================================
  // EDIT MODE
  // ==========================================================

  if (isUser && isEditing) {

    return (
      <div className="user-message">

        <div className="bubble-user edit-message-bubble">

          <textarea
            value={editText}
            onChange={(e) =>
              setEditText(e.target.value)
            }
            autoFocus
            rows={Math.max(
              2,
              Math.min(
                8,
                editText.split("\n").length
              )
            )}
            className="edit-message-input"
          />

          <div className="edit-message-actions">

            <button
              type="button"
              onClick={() =>
                onEdit?.(
                  id,
                  editText.trim()
                )
              }
              disabled={!editText.trim()}
            >
              Send
            </button>

            <button
              type="button"
              onClick={() =>
                onEdit?.(
                  id,
                  null
                )
              }
            >
              Cancel
            </button>

          </div>

        </div>

      </div>
    );
  }


  return (
    <div
      className={
        isUser
          ? "user-message"
          : "ai-message"
      }
    >

      <div
        className={isUser ? "bubble-user" : `bubble-ai ${content.trim().length < 120 ? "bubble-ai-short" : ""}`}
      >

        {/* ================================================== */}
        {/* ATTACHMENTS */}
        {/* ================================================== */}

        {isUser &&
          Array.isArray(attachments) &&
          attachments.length > 0 && (

          <div className="message-attachments">

            {attachments.map(
              (attachment, index) => {

                const filename =
                  attachment.name ||
                  attachment.filename ||
                  "Attached file";

                return (
                  <div
                    className="message-attachment"
                    key={
                      attachment.id ||
                      `${filename}-${index}`
                    }
                  >

                    <div className="message-attachment-icon">
                      File
                    </div>

                    <div className="message-attachment-info">

                      <div className="message-attachment-name">
                        {filename}
                      </div>

                      <div className="message-attachment-status">
                        Attached
                      </div>

                    </div>

                  </div>
                );

              }
            )}

          </div>

        )}


        {/* ================================================== */}
        {/* MESSAGE CONTENT */}
        {/* ================================================== */}

        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{

            code({
              children,
              className,
            }) {

              const codeText =
                String(children).replace(
                  /\n$/,
                  ""
                );

              const match =
                /language-(\w+)/.exec(
                  className || ""
                );

              if (match) {

                const copyCode = async () => {

                  try {

                    await navigator.clipboard.writeText(
                      codeText
                    );

                    setCopiedCode(codeText);

                    setTimeout(() => {
                      setCopiedCode("");
                    }, 2000);

                  } catch (error) {

                    console.error(
                      "Failed to copy code:",
                      error
                    );

                  }

                };

                return (
                  <div
                    style={{
                      position: "relative",
                      maxWidth: "100%",
                    }}
                  >

                    <button
                      type="button"
                      onClick={copyCode}
                      style={{
                        position: "absolute",
                        top: "8px",
                        right: "8px",
                        zIndex: 10,
                        padding: "5px 10px",
                        border: "none",
                        borderRadius: "6px",
                        background:
                          copiedCode === codeText
                            ? "#22c55e"
                            : "#374151",
                        color: "white",
                        fontSize: "12px",
                        cursor: "pointer",
                      }}
                    >
                      {copiedCode === codeText
                        ? "Copied!"
                        : "Copy"}
                    </button>

                    <SyntaxHighlighter
                      language={match[1]}
                      style={oneDark}
                      PreTag="div"
                      wrapLongLines={true}
                      customStyle={{
                        margin: 0,
                        borderRadius: "8px",
                        overflowX: "auto",
                        maxWidth: "100%",
                        paddingTop: "42px",
                      }}
                    >
                      {codeText}
                    </SyntaxHighlighter>

                  </div>
                );
              }

              return (
                <code
                  className={className}
                >
                  {children}
                </code>
              );
            },


            table({ children }) {

              return (
                <div className="markdown-table-wrapper">
                  <table>
                    {children}
                  </table>
                </div>
              );
            },

          }}
        >
          {content}
        </ReactMarkdown>


        {/* ================================================== */}
        {/* USER MESSAGE ACTIONS */}
        {/* ================================================== */}

        {isUser && id && (

          <div className="message-actions">

            <button
              type="button"
              onClick={() =>
                onEdit?.(
                  id,
                  undefined
                )
              }
              title="Edit message"
            >
              Edit</button>

          </div>

        )}


        {/* ================================================== */}
        {/* AI MESSAGE ACTIONS */}
        {/* ================================================== */}

        {!isUser && id && (

          <div className="message-actions">

            <button
              type="button"
              onClick={() => {

                if (
                  navigator.clipboard &&
                  content
                ) {
                  navigator.clipboard.writeText(
                    content
                  );
                }

              }}
              title="Copy response"
            >
              Copy
            </button>


            {onRegenerate && (

              <button
                type="button"
                onClick={() =>
                  onRegenerate(id)
                }
                disabled={isRegenerating}
                title="Regenerate response"
              >
                {isRegenerating
                  ? "..."
                  : "Retry"}
              </button>

            )}

          </div>

        )}

      </div>

    </div>
  );
}


export default Message;





