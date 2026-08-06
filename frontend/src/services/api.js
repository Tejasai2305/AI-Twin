import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// -----------------------------
// Conversation APIs
// -----------------------------

export const getConversations = () =>
  api.get("/conversations");

export const createConversation = (title) =>
  api.post("/conversation", { title });

export const getConversation = (id) =>
  api.get(`/conversation/${id}`);

// -----------------------------
// Normal Ask API (Keep this)
// -----------------------------

export const askQuestion = (conversationId, question) =>
  api.post("/ask", {
    conversation_id: conversationId,
    question,
  });

// -----------------------------
// Streaming Ask API
// -----------------------------

export const askQuestionStream = async (
  conversationId,
  question,
  onChunk,
  signal
) => {
  const response = await fetch("http://127.0.0.1:8000/ask-stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      question,
    }),
    signal,
  });

  console.log("Connected to stream");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let fullResponse = "";

  while (true) {
    const { done, value } = await reader.read();

    console.log("Reader:", done);

    if (done) break;

    const chunk = decoder.decode(value, { stream: true });

    console.log("Chunk:", chunk);

    fullResponse += chunk;

    onChunk(fullResponse);
  }

  return fullResponse;
};
// -----------------------------
// Memory APIs
// -----------------------------

export const getMemories = () =>
  api.get("/memories");

export const createMemory = (memory, importance = 5) =>
  api.post("/memory", {
    memory,
    importance,
  });

export const deleteMemory = (id) =>
  api.delete(`/memory/${id}`);

export const updateMemory = (id, memory, importance) =>
  api.put(`/memory/${id}`, {
    memory,
    importance,
  });
  export const searchMemories = (query) =>
  api.get(`/memory/search?query=${encodeURIComponent(query)}`);