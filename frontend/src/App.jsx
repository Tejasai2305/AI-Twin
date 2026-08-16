import { useState, useRef } from "react";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import MemoryPanel from "./components/MemoryPanel";
import "./App.css";
import Header from "./components/Header";
import ToolStatus from "./components/ToolStatus";
import {
  askQuestionStream,
  getConversation,
} from "./services/api";

function App() {
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [controller, setController] = useState(null);

  const [currentPage, setCurrentPage] = useState("chat");

  // 👇 Add this here
  const [toolStatus, setToolStatus] = useState("");

  const sidebarRef = useRef(null);

  const loadConversation = async (id) => {
    try {
      const response = await getConversation(id);

      setConversationId(id);
      setMessages(response.data);
      setCurrentPage("chat");
    } catch (error) {
      console.error(error);
      alert("Failed to load conversation.");
    }
  };

  const sendMessage = async (question) => {
    if (!conversationId) {
      alert("Please create or select a conversation.");
      return;
    }

    const abortController = new AbortController();

    setController(abortController);
    setIsStreaming(true);
    setToolStatus("Thinking...");

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: question,
      },
      {
        role: "assistant",
        content: "",
      },
    ]);

    try {
      await askQuestionStream(
        conversationId,
        question,
        (partialAnswer) => {
          setMessages((prev) => {
            const updated = [...prev];

            updated[updated.length - 1] = {
              role: "assistant",
              content: partialAnswer,
            };

            return updated;
          });
        },
        abortController.signal
      );

      sidebarRef.current?.refresh();
      setToolStatus("");
      setIsStreaming(false);
      setController(null);

    } catch (err) {

      if (err.name === "AbortError") {
        setToolStatus("");
        setIsStreaming(false);
        setController(null);
        return;
      }

      console.error(err);

      setMessages((prev) => {
        const updated = [...prev];

        updated[updated.length - 1] = {
          role: "assistant",
          content: "❌ Failed to get response.",
        };

        return updated;
      });

      setIsStreaming(false);
      setController(null);
    }
  };

  const stopGeneration = () => {
    if (controller) {
      controller.abort();
    }
  };

  return (
    <div className="app">

      <Sidebar
        ref={sidebarRef}
        onSelectConversation={loadConversation}
        onShowMemories={() => setCurrentPage("memory")}
      />

      <div className="main">
         <Header />

        {currentPage === "chat" ? (
          <>
            <ToolStatus status={toolStatus} />
            <ChatWindow messages={messages} />

            <ChatInput
              onSend={sendMessage}
              isStreaming={isStreaming}
              onStop={stopGeneration}
            />
          </>
        ) : (
          <MemoryPanel />
        )}

      </div>

    </div>
  );
}

export default App;