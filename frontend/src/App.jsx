import { useState, useRef, useEffect } from "react";

import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import MemoryPanel from "./components/MemoryPanel";
import KnowledgeGraphPanel from "./components/KnowledgeGraphPanel";
import TimelinePanel from "./components/TimelinePanel";
import ProfilePanel from "./components/ProfilePanel";
import DocumentCenterPanel from "./components/DocumentCenterPanel";
import GlobalSearchPanel from "./components/GlobalSearchPanel";
import DashboardPanel from "./components/DashboardPanel";
import InsightsPanel from "./components/InsightsPanel";
import DecisionSupportPanel from "./components/DecisionSupportPanel";
import AuthGate from "./components/AuthGate";
import ResetPassword from "./components/ResetPassword";
import Header from "./components/Header";
import ToolStatus from "./components/ToolStatus";

import "./App.css";

import {
  askQuestionStream,
  getConversation,
  uploadPDF,
  editMessageStream,
  regenerateResponseStream,
} from "./services/api";
import { isLoggedIn, logout, getMe } from "./services/authApi";


function App() {
  const SKIP_KEY = "ai_twin_skip_auth";

  const [authChecked, setAuthChecked] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [skippedAuth, setSkippedAuth] = useState(
    localStorage.getItem(SKIP_KEY) === "true"
  );

  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [attachments, setAttachments] = useState([]);

  const [isStreaming, setIsStreaming] = useState(false);
  const [controller, setController] = useState(null);

  const [regeneratingMessageId, setRegeneratingMessageId] =
    useState(null);

  // ID of the user message currently being edited
  const [editingMessageId, setEditingMessageId] =
    useState(null);

  const [currentPage, setCurrentPage] = useState("chat");
  const [toolStatus, setToolStatus] = useState("");

  const sidebarRef = useRef(null);

  // ==========================================================
  // AUTH: check for an existing valid token on load, so a
  // refresh doesn't force the person to log in again.
  // ==========================================================

  useEffect(() => {
    if (!isLoggedIn()) {
      setAuthChecked(true);
      return;
    }

    getMe()
      .then((res) => {
        setCurrentUser(res.data);
        setAuthenticated(true);
      })
      .catch(() => {
        // Stored token is invalid/expired.
        logout();
      })
      .finally(() => setAuthChecked(true));
  }, []);

  const handleSkip = () => {
    localStorage.setItem(SKIP_KEY, "true");
    setSkippedAuth(true);
  };

  const handleLogout = () => {
    logout();
    setAuthenticated(false);
    setCurrentUser(null);
    localStorage.removeItem(SKIP_KEY);
    setSkippedAuth(false);
    setMessages([]);
    setConversationId(null);
  };


  // ==========================================================
  // LOAD CONVERSATION
  // ==========================================================

  const loadConversation = async (id) => {
    try {
      const response = await getConversation(id);

      console.log(
        "LOADED CONVERSATION:",
        response.data
      );

      const loadedMessages =
        (response.data.messages || []).map(
          (message) => ({
            id: message.id,
            role: message.role,
            content: message.content,
            created_at: message.created_at,

            attachments:
              Array.isArray(message.attachments)
                ? message.attachments.map(
                    (attachment) => ({
                      id: attachment.id,

                      name:
                        attachment.name ||
                        attachment.filename ||
                        "Attached file",

                      filename:
                        attachment.filename ||
                        attachment.name ||
                        "Attached file",

                      file_type:
                        attachment.file_type ||
                        "application/pdf",
                    })
                  )
                : [],
          })
        );

      console.log(
        "MESSAGES AFTER NORMALIZATION:",
        loadedMessages
      );

      setConversationId(id);
      setMessages(loadedMessages);

      setAttachments(
        response.data.attachments || []
      );

      setEditingMessageId(null);

      setCurrentPage("chat");

    } catch (error) {
      console.error(
        "Failed to load conversation:",
        error
      );

      alert(
        "Failed to load conversation."
      );
    }
  };


  // ==========================================================
  // UPLOAD ATTACHMENT
  // ==========================================================

  const uploadAttachment = async (
    file,
    onProgress
  ) => {
    try {
      if (!conversationId) {
        alert(
          "Please create or select a conversation before uploading a file."
        );

        return null;
      }

      setToolStatus(
        `Uploading ${file.name}...`
      );

      const response =
        await uploadPDF(
          file,
          conversationId,
          onProgress
        );

      console.log(
        "PDF upload response:",
        response.data
      );

      setToolStatus("");

      // Refresh conversation so attachment
      // information is immediately available.
      await loadConversation(
        conversationId
      );

      return response.data;

    } catch (error) {
      console.error(
        "PDF upload failed:",
        error
      );

      setToolStatus("");

      const detail =
        error.response?.data?.detail;

      let errorMessage =
        "Unknown upload error.";

      if (typeof detail === "string") {
        errorMessage = detail;

      } else if (Array.isArray(detail)) {
        errorMessage = detail
          .map(
            (item) =>
              item.msg ||
              JSON.stringify(item)
          )
          .join(", ");

      } else if (detail) {
        errorMessage =
          JSON.stringify(detail);
      }

      alert(
        `Failed to upload ${file.name}.\n\n${errorMessage}`
      );

      throw error;
    }
  };


  // ==========================================================
  // SEND NEW MESSAGE
  // ==========================================================

  const sendMessage = async (
    question,
    attachedFiles = []
  ) => {
    if (!conversationId) {
      alert(
        "Please create or select a conversation."
      );

      return;
    }

    if (isStreaming) {
      return;
    }

    const trimmedQuestion =
      question.trim();

    if (!trimmedQuestion) {
      return;
    }

    const abortController =
      new AbortController();

    setController(abortController);
    setIsStreaming(true);
    setToolStatus("Thinking...");

    // Add temporary messages to UI
    setMessages((prev) => [
      ...prev,

      {
        role: "user",
        content: trimmedQuestion,

        attachments:
          attachedFiles.map(
            (file) => ({
              name: file.name,
              filename: file.name,
              type: file.type,
              size: file.size,
            })
          ),
      },

      {
        role: "assistant",
        content: "",
      },
    ]);

    try {
      await askQuestionStream(
        conversationId,
        trimmedQuestion,

        (partialAnswer) => {
          setMessages((prev) => {
            const updated = [...prev];

            if (updated.length === 0) {
              return updated;
            }

            const lastIndex =
              updated.length - 1;

            updated[lastIndex] = {
              ...updated[lastIndex],
              role: "assistant",
              content: partialAnswer,
            };

            return updated;
          });
        },

        abortController.signal
      );

      // Reload from database so the messages
      // have their real database IDs.
      await loadConversation(
        conversationId
      );

      sidebarRef.current?.refresh();

      setToolStatus("");
      setIsStreaming(false);
      setController(null);

    } catch (err) {
      if (
        err.name === "AbortError"
      ) {
        setToolStatus("");
        setIsStreaming(false);
        setController(null);

        return;
      }

      console.error(
        "Chat error:",
        err
      );

      setMessages((prev) => {
        const updated = [...prev];

        if (updated.length === 0) {
          return updated;
        }

        updated[updated.length - 1] = {
          ...updated[
            updated.length - 1
          ],

          role: "assistant",

          content:
            "âŒ Failed to get response.",
        };

        return updated;
      });

      setToolStatus("");
      setIsStreaming(false);
      setController(null);
    }
  };


  // ==========================================================
  // STOP GENERATION
  // ==========================================================

  const stopGeneration = () => {
    if (controller) {
      controller.abort();
    }
  };


  // ==========================================================
  // EDIT USER MESSAGE
  //
  // onEdit(id, undefined)
  //     -> enter edit mode
  //
  // onEdit(id, null)
  //     -> cancel edit
  //
  // onEdit(id, "new question")
  //     -> update question and regenerate answer
  // ==========================================================

  const editMessage = async (
    userMessageId,
    newQuestion
  ) => {

    // --------------------------------------------------------
    // ENTER EDIT MODE
    // --------------------------------------------------------

    if (typeof newQuestion === "undefined") {
      if (isStreaming) {
        return;
      }

      setEditingMessageId(
        userMessageId
      );

      return;
    }


    // --------------------------------------------------------
    // CANCEL EDIT
    // --------------------------------------------------------

    if (newQuestion === null) {
      setEditingMessageId(null);

      return;
    }


    // --------------------------------------------------------
    // VALIDATION
    // --------------------------------------------------------

    if (!conversationId) {
      return;
    }

    const trimmedQuestion =
      newQuestion.trim();

    if (!trimmedQuestion) {
      return;
    }

    if (isStreaming) {
      return;
    }


    // --------------------------------------------------------
    // FIND USER MESSAGE
    // --------------------------------------------------------

    const userMessageIndex =
      messages.findIndex(
        (message) =>
          message.id ===
          userMessageId
      );

    if (
      userMessageIndex === -1
    ) {
      console.error(
        "User message not found:",
        userMessageId
      );

      return;
    }


    // --------------------------------------------------------
    // FIND THE ASSISTANT MESSAGE THAT
    // BELONGS TO THIS USER MESSAGE
    //
    // Your backend structure is:
    //
    // USER
    // ASSISTANT
    //
    // Therefore the assistant is normally
    // the next message.
    // --------------------------------------------------------

    let assistantMessageIndex =
      -1;

    if (
      userMessageIndex + 1 <
      messages.length
    ) {
      const nextMessage =
        messages[
          userMessageIndex + 1
        ];

      if (
        nextMessage.role ===
        "assistant"
      ) {
        assistantMessageIndex =
          userMessageIndex + 1;
      }
    }


    if (
      assistantMessageIndex === -1
    ) {
      console.error(
        "Assistant message belonging to edited user message was not found."
      );

      alert(
        "Could not find the response belonging to this question."
      );

      return;
    }


    const assistantMessage =
      messages[
        assistantMessageIndex
      ];

    const assistantMessageId =
      assistantMessage.id;


    if (!assistantMessageId) {
      console.error(
        "Assistant message has no database ID."
      );

      alert(
        "This response cannot be edited yet. Please reload the conversation and try again."
      );

      return;
    }


    console.log(
      "EDITING MESSAGE:",
      userMessageId
    );

    console.log(
      "ASSISTANT MESSAGE:",
      assistantMessageId
    );

    console.log(
      "NEW QUESTION:",
      trimmedQuestion
    );


    // --------------------------------------------------------
    // START EDIT STREAM
    // --------------------------------------------------------

    const abortController =
      new AbortController();

    setController(
      abortController
    );

    setIsStreaming(true);

    setEditingMessageId(
      null
    );

    setRegeneratingMessageId(
      assistantMessageId
    );

    setToolStatus(
      "Updating question..."
    );


    // --------------------------------------------------------
    // UPDATE UI IMMEDIATELY
    // --------------------------------------------------------

    setMessages((prev) => {
      const updated = [...prev];

      if (
        userMessageIndex <
        updated.length
      ) {
        updated[
          userMessageIndex
        ] = {
          ...updated[
            userMessageIndex
          ],

          content:
            trimmedQuestion,
        };
      }

      if (
        assistantMessageIndex <
        updated.length
      ) {
        updated[
          assistantMessageIndex
        ] = {
          ...updated[
            assistantMessageIndex
          ],

          content: "",
        };
      }

      return updated;
    });


    // --------------------------------------------------------
    // CALL BACKEND EDIT ENDPOINT
    // --------------------------------------------------------

    try {
      await editMessageStream(
        conversationId,
        userMessageId,
        trimmedQuestion,

        (partialAnswer) => {
          setMessages((prev) => {
            const updated = [
              ...prev,
            ];

            const index =
              updated.findIndex(
                (message) =>
                  message.id ===
                  assistantMessageId
              );

            if (index !== -1) {
              updated[index] = {
                ...updated[index],

                content:
                  partialAnswer,
              };
            }

            return updated;
          });
        },

        abortController.signal
      );


      // ------------------------------------------------------
      // STREAM FINISHED
      //
      // Reload database state so the UI exactly matches
      // SQLite.
      // ------------------------------------------------------

      await loadConversation(
        conversationId
      );

      sidebarRef.current?.refresh();

      setToolStatus("");
      setIsStreaming(false);
      setController(null);

      setRegeneratingMessageId(
        null
      );

    } catch (err) {

      // ------------------------------------------------------
      // USER STOPPED GENERATION
      // ------------------------------------------------------

      if (
        err.name === "AbortError"
      ) {
        setToolStatus("");
        setIsStreaming(false);
        setController(null);

        setRegeneratingMessageId(
          null
        );

        // Restore database state
        await loadConversation(
          conversationId
        );

        return;
      }


      // ------------------------------------------------------
      // EDIT FAILED
      // ------------------------------------------------------

      console.error(
        "Edit message failed:",
        err
      );

      setToolStatus("");
      setIsStreaming(false);
      setController(null);

      setRegeneratingMessageId(
        null
      );

      alert(
        err.message ||
        "Failed to edit message."
      );

      // Restore the UI from database
      await loadConversation(
        conversationId
      );
    }
  };


  // ==========================================================
  // REGENERATE AI RESPONSE
  // ==========================================================

  const regenerateMessage = async (
    assistantMessageId
  ) => {

    if (!conversationId) {
      return;
    }

    if (isStreaming) {
      return;
    }

    const messageIndex =
      messages.findIndex(
        (message) =>
          message.id ===
          assistantMessageId
      );

    if (
      messageIndex === -1
    ) {
      console.error(
        "Assistant message not found:",
        assistantMessageId
      );

      return;
    }

    const abortController =
      new AbortController();

    setController(
      abortController
    );

    setIsStreaming(true);

    setRegeneratingMessageId(
      assistantMessageId
    );

    setToolStatus(
      "Regenerating response..."
    );


    // Clear current response
    setMessages((prev) => {
      const updated = [...prev];

      updated[messageIndex] = {
        ...updated[messageIndex],
        content: "",
      };

      return updated;
    });


    try {
      await regenerateResponseStream(
        conversationId,
        assistantMessageId,

        (partialAnswer) => {
          setMessages((prev) => {
            const updated = [
              ...prev,
            ];

            const index =
              updated.findIndex(
                (message) =>
                  message.id ===
                  assistantMessageId
              );

            if (index !== -1) {
              updated[index] = {
                ...updated[index],

                content:
                  partialAnswer,
              };
            }

            return updated;
          });
        },

        abortController.signal
      );


      // Reload database state
      await loadConversation(
        conversationId
      );

      sidebarRef.current?.refresh();

      setToolStatus("");
      setIsStreaming(false);
      setController(null);

      setRegeneratingMessageId(
        null
      );

    } catch (err) {

      if (
        err.name === "AbortError"
      ) {
        setToolStatus("");
        setIsStreaming(false);
        setController(null);

        setRegeneratingMessageId(
          null
        );

        await loadConversation(
          conversationId
        );

        return;
      }


      console.error(
        "Regeneration failed:",
        err
      );

      setToolStatus("");
      setIsStreaming(false);
      setController(null);

      setRegeneratingMessageId(
        null
      );

      alert(
        "Failed to regenerate response."
      );

      await loadConversation(
        conversationId
      );
    }
  };


  // ==========================================================
  // UI
  // ==========================================================

  if (window.location.pathname === "/reset-password") {
    return <ResetPassword />;
  }

  if (!authChecked) {
    return null;
  }

  if (!authenticated && !skippedAuth) {
    return (
      <AuthGate
        onAuthenticated={(user) => {
          setCurrentUser(user);
          setAuthenticated(true);
        }}
        onSkip={handleSkip}
      />
    );
  }

  return (
    <div className="app">

      <Sidebar
        ref={sidebarRef}
        onSelectConversation={
          loadConversation
        }
        onShowMemories={() =>
          setCurrentPage("memory")
        }
        onShowGraph={() =>
          setCurrentPage("graph")
        }
        onShowTimeline={() =>
          setCurrentPage("timeline")
        }
        onShowProfile={() =>
          setCurrentPage("profile")
        }
        onShowDocuments={() =>
          setCurrentPage("documents")
        }
        onShowSearch={() =>
          setCurrentPage("search")
        }
        onShowDashboard={() =>
          setCurrentPage("dashboard")
        }
        onShowInsights={() =>
          setCurrentPage("insights")
        }
        onShowDecisions={() =>
          setCurrentPage("decisions")
        }
        onShowChat={() =>
          setCurrentPage("chat")
        }
      />


      <div className="main">

        <Header currentUser={authenticated ? currentUser : null} onLogout={handleLogout} isStreaming={isStreaming} />


        {currentPage === "chat" ? (

          <>

            <ToolStatus
              status={toolStatus}
            />


            <ChatWindow
              messages={messages}

              onRegenerate={
                regenerateMessage
              }

              onEdit={
                editMessage
              }

              editingMessageId={
                editingMessageId
              }

              regeneratingMessageId={regeneratingMessageId}
              isStreaming={isStreaming}
            />


            <ChatInput
              onSend={sendMessage}

              onUpload={
                uploadAttachment
              }

              isStreaming={
                isStreaming
              }

              onStop={
                stopGeneration
              }
            />

          </>

        ) : currentPage === "memory" ? (

          <MemoryPanel />

        ) : currentPage === "graph" ? (

          <KnowledgeGraphPanel />

        ) : currentPage === "profile" ? (

          <ProfilePanel onEditMemories={() => setCurrentPage("memory")} />

        ) : currentPage === "documents" ? (

          <DocumentCenterPanel />

        ) : currentPage === "search" ? (

          <GlobalSearchPanel
            onOpenConversation={async (conversationId) => {
              await loadConversation(conversationId);
              setCurrentPage("chat");
            }}
          />

        ) : currentPage === "dashboard" ? (

          <DashboardPanel onNavigate={(page) => setCurrentPage(page)} />

        ) : currentPage === "insights" ? (

          <InsightsPanel onNavigate={(page) => setCurrentPage(page)} />

        ) : currentPage === "decisions" ? (

          <DecisionSupportPanel />

        ) : (

          <TimelinePanel />

        )}

      </div>

    </div>
  );
}


export default App;





