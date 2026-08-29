import { useRef, useState } from "react";

function ChatInput({
  onSend,
  onUpload,
  isStreaming,
  onStop,
}) {
  const [text, setText] = useState("");
  const [attachments, setAttachments] = useState([]);
  const [uploading, setUploading] = useState(false);

  const fileInputRef = useRef(null);

  // -----------------------------------
  // Select files
  // -----------------------------------

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files || []);

    if (files.length === 0) {
      return;
    }

    // Prevent the same file from being uploaded twice
    const newFiles = files.filter((file) => {
      return !attachments.some(
        (item) =>
          item.file?.name === file.name &&
          item.file?.size === file.size &&
          item.file?.lastModified === file.lastModified
      );
    });

    if (newFiles.length === 0) {
      e.target.value = "";
      return;
    }

    setUploading(true);

    try {
      for (const file of newFiles) {
        const attachmentId =
          `${file.name}-${file.size}-${file.lastModified}-${Date.now()}-${Math.random()}`;

        // -----------------------------------
        // Add file to UI immediately
        // -----------------------------------

        setAttachments((prev) => [
          ...prev,
          {
            id: attachmentId,
            file: file,
            uploaded: false,
            progress: 0,
            filename: file.name,
          },
        ]);

        try {
          // -----------------------------------
          // Upload file
          // -----------------------------------

          const uploadedFile = await onUpload(
            file,
            (progress) => {
              setAttachments((prev) =>
                prev.map((item) =>
                  item.id === attachmentId
                    ? {
                        ...item,
                        progress: progress,
                      }
                    : item
                )
              );
            }
          );

          // -----------------------------------
          // Upload completed
          // -----------------------------------

          setAttachments((prev) =>
            prev.map((item) =>
              item.id === attachmentId
                ? {
                    ...item,
                    uploaded: true,
                    progress: 100,
                    filename:
                      uploadedFile?.filename || file.name,
                  }
                : item
            )
          );
        } catch (error) {
          console.error(
            `Upload failed for ${file.name}:`,
            error
          );

          // Remove failed upload from UI
          setAttachments((prev) =>
            prev.filter(
              (item) => item.id !== attachmentId
            )
          );
        }
      }
    } finally {
      setUploading(false);
    }

    // Allow selecting the same file again later
    e.target.value = "";
  };

  // -----------------------------------
  // Remove attachment
  // -----------------------------------

  const removeAttachment = (index) => {
    setAttachments((prev) =>
      prev.filter((_, i) => i !== index)
    );
  };

  // -----------------------------------
  // Send message
  // -----------------------------------

  const handleSend = () => {
    const trimmedText = text.trim();

    // Don't send an empty message
    if (!trimmedText) {
      return;
    }

    // Don't send while files are uploading
    if (uploading) {
      return;
    }

    // Only send successfully uploaded files
    const uploadedFiles = attachments
      .filter((item) => item.uploaded)
      .map((item) => item.file);

    onSend(
      trimmedText,
      uploadedFiles
    );

    // Clear input attachments.
    // They will now belong to the sent message
    // and be displayed by Message.jsx.
    setText("");
    setAttachments([]);
  };

  // -----------------------------------
  // Keyboard handling
  // -----------------------------------

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();

      if (isStreaming) {
        onStop();
      } else {
        handleSend();
      }
    }
  };

  // -----------------------------------
  // UI
  // -----------------------------------

  return (
    <div className="chat-input-container">

      {/* -------------------------------- */}
      {/* Pending attachments */}
      {/* -------------------------------- */}

      {attachments.length > 0 && (
        <div className="attachment-list">

          {attachments.map((item, index) => (
            <div
              className="attachment-item"
              key={item.id}
            >

              {/* File icon */}
              <span className="attachment-icon">
                📄
              </span>

              {/* File information */}
              <div className="attachment-details">

                <span className="attachment-name">
                  {item.filename}
                </span>

                {/* Upload progress */}
                {!item.uploaded && (
                  <>
                    <div className="attachment-progress-container">
                      <div
                        className="attachment-progress"
                        style={{
                          width: `${item.progress}%`,
                        }}
                      />
                    </div>

                    <span className="attachment-progress-text">
                      {item.progress}%
                    </span>
                  </>
                )}

                {/* Upload completed */}
                {item.uploaded && (
                  <span className="attachment-uploaded">
                    Uploaded
                  </span>
                )}

              </div>

              {/* Green check */}
              {item.uploaded && (
                <span className="attachment-check">
                  ✓
                </span>
              )}

              {/* Remove file */}
              <button
                type="button"
                className="attachment-remove"
                onClick={() =>
                  removeAttachment(index)
                }
                title="Remove file"
              >
                ×
              </button>

            </div>
          ))}

        </div>
      )}

      {/* -------------------------------- */}
      {/* Chat input */}
      {/* -------------------------------- */}

      <div className="chat-input">

        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt"
          onChange={handleFileSelect}
          style={{ display: "none" }}
        />

        {/* Attach button */}
        <button
          type="button"
          className="attach-button"
          onClick={() =>
            fileInputRef.current?.click()
          }
          disabled={
            isStreaming || uploading
          }
          title="Attach file"
        >
          📎
        </button>

        {/* Text input */}
        <textarea
          value={text}
          placeholder="Ask anything..."
          onChange={(e) =>
            setText(e.target.value)
          }
          onKeyDown={handleKeyDown}
          disabled={isStreaming}
        />

        {/* Send / Stop */}
        {isStreaming ? (
          <button
            type="button"
            onClick={onStop}
            style={{
              backgroundColor: "#dc2626",
            }}
          >
            Stop
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSend}
            disabled={
              uploading ||
              !text.trim()
            }
          >
            Send
          </button>
        )}

      </div>
    </div>
  );
}

export default ChatInput;