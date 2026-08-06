import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

function Message({ role, content }) {
  const isUser = role === "user";

  return (
    <div className={isUser ? "user-message" : "ai-message"}>
      <div className={isUser ? "bubble-user" : "bubble-ai"}>
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
}

export default Message;