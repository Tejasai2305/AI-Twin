import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});


// ============================================================
// CONVERSATION APIs
// ============================================================

export const getConversations = () =>
  api.get("/conversations");


export const searchConversations = (query) =>
  api.get(
    `/conversations/search?q=${encodeURIComponent(query)}`
  );


export const createConversation = (title) =>
  api.post("/conversation", {
    title,
  });


export const getConversation = (id) =>
  api.get(`/conversation/${id}`);


export const renameConversation = (
  id,
  title
) =>
  api.put(`/conversation/${id}`, {
    title,
  });


export const deleteConversation = (id) =>
  api.delete(`/conversation/${id}`);


// ============================================================
// NORMAL ASK API
// ============================================================

export const askQuestion = (
  conversationId,
  question
) =>
  api.post("/ask", {
    conversation_id: conversationId,
    question,
  });


// ============================================================
// STREAMING ASK API
// ============================================================

export const askQuestionStream = async (
  conversationId,
  question,
  onChunk,
  signal
) => {

  const response = await fetch(
    `${API_BASE_URL}/ask-stream`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        conversation_id: conversationId,
        question,
      }),

      signal,
    }
  );


  if (!response.ok) {

    let errorMessage =
      `Request failed with status ${response.status}`;

    try {

      const errorData =
        await response.json();

      if (errorData.detail) {
        errorMessage =
          String(errorData.detail);
      }

    } catch {
      // Keep default error message
    }

    throw new Error(errorMessage);
  }


  console.log(
    "Connected to stream"
  );


  if (!response.body) {
    throw new Error(
      "Streaming response body is unavailable."
    );
  }


  const reader =
    response.body.getReader();

  const decoder =
    new TextDecoder();

  let fullResponse = "";


  while (true) {

    const {
      done,
      value,
    } = await reader.read();


    if (done) {
      break;
    }


    const chunk =
      decoder.decode(
        value,
        {
          stream: true,
        }
      );


    fullResponse += chunk;

    onChunk(fullResponse);
  }


  return fullResponse;
};


// ============================================================
// REGENERATE AI RESPONSE
// ============================================================

export const regenerateResponseStream = async (
  conversationId,
  assistantMessageId,
  onChunk,
  signal
) => {

  const response = await fetch(
    `${API_BASE_URL}/regenerate-stream`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        conversation_id:
          conversationId,

        assistant_message_id:
          assistantMessageId,
      }),

      signal,
    }
  );


  if (!response.ok) {

    let errorMessage =
      `Regeneration failed with status ${response.status}`;

    try {

      const errorData =
        await response.json();

      if (errorData.detail) {
        errorMessage =
          String(errorData.detail);
      }

    } catch {
      // Keep default error message
    }

    throw new Error(errorMessage);
  }


  console.log(
    "Connected to regeneration stream"
  );


  if (!response.body) {
    throw new Error(
      "Regeneration response body is unavailable."
    );
  }


  const reader =
    response.body.getReader();

  const decoder =
    new TextDecoder();

  let fullResponse = "";


  while (true) {

    const {
      done,
      value,
    } = await reader.read();


    if (done) {
      break;
    }


    const chunk =
      decoder.decode(
        value,
        {
          stream: true,
        }
      );


    fullResponse += chunk;

    onChunk(fullResponse);
  }


  return fullResponse;
};


// ============================================================
// EDIT USER MESSAGE AND RESEND
// ============================================================

export const editMessageStream = async (
  conversationId,
  userMessageId,
  question,
  onChunk,
  signal
) => {

  const response = await fetch(
    `${API_BASE_URL}/edit-message-stream`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        conversation_id:
          conversationId,

        user_message_id:
          userMessageId,

        question,
      }),

      signal,
    }
  );


  if (!response.ok) {

    let errorMessage =
      `Edit request failed with status ${response.status}`;

    try {

      const errorData =
        await response.json();

      if (errorData.detail) {
        errorMessage =
          String(errorData.detail);
      }

    } catch {
      // Keep default error message
    }

    throw new Error(errorMessage);
  }


  console.log(
    "Connected to edit/resend stream"
  );


  if (!response.body) {
    throw new Error(
      "Edit response body is unavailable."
    );
  }


  const reader =
    response.body.getReader();

  const decoder =
    new TextDecoder();

  let fullResponse = "";


  while (true) {

    const {
      done,
      value,
    } = await reader.read();


    if (done) {
      break;
    }


    const chunk =
      decoder.decode(
        value,
        {
          stream: true,
        }
      );


    fullResponse += chunk;

    onChunk(fullResponse);
  }


  return fullResponse;
};


// ============================================================
// MEMORY APIs
// ============================================================

export const getMemories = () =>
  api.get("/memories");


export const createMemory = (
  memory,
  importance = 5
) =>
  api.post("/memory", {
    memory,
    importance,
  });


export const deleteMemory = (
  id
) =>
  api.delete(`/memory/${id}`);


export const updateMemory = (
  id,
  memory,
  importance
) =>
  api.put(`/memory/${id}`, {
    memory,
    importance,
  });


export const searchMemories = (
  query
) =>
  api.get(
    `/memory/search?query=${encodeURIComponent(
      query
    )}`
  );


// ============================================================
// FILE UPLOAD API
// ============================================================

export const uploadPDF = async (
  file,
  conversationId,
  onProgress
) => {

  const formData =
    new FormData();


  formData.append(
    "file",
    file
  );


  formData.append(
    "conversation_id",
    conversationId
  );


  return api.post(
    "/upload-pdf",
    formData,
    {
      onUploadProgress:
        (progressEvent) => {

          if (
            !progressEvent.total
          ) {
            return;
          }


          const percent =
            Math.round(
              (
                progressEvent.loaded *
                100
              ) /
              progressEvent.total
            );


          onProgress?.(
            percent
          );
        },
    }
  );
};