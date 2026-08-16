import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

function Message({ role, content }) {
  const isUser = role === "user";

  return (
    <div className={isUser ? "user-message" : "ai-message"}>
      <div className={isUser ? "bubble-user" : "bubble-ai"}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ children, className }) {
              const match = /language-(\w+)/.exec(className || "");

              if (match) {
                return (
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
                    }}
                  >
                    {String(children).replace(/\n$/, "")}
                  </SyntaxHighlighter>
                );
              }

              return (
                <code className={className}>
                  {children}
                </code>
              );
            },

            table({ children }) {
              return (
                <div className="markdown-table-wrapper">
                  <table>{children}</table>
                </div>
              );
            },
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}

export default Message;