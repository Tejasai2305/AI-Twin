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

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files || []);

    if (files.length === 0) return;

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

        setAttachments((prev) => [
          ...prev,
          {
            id: attachmentId,
            file,
            uploaded: false,
            progress: 0,
            filename: file.name,
          },
        ]);

        try {
          const uploadedFile = await onUpload(file, (progress) => {
            setAttachments((prev) =>
              prev.map((item) =>
                item.id === attachmentId
                  ? { ...item, progress }
                  : item
              )
            );
          });

          setAttachments((prev) =>
            prev.map((item) =>
              item.id === attachmentId
                ? {
                    ...item,
                    uploaded: true,
                    progress: 100,
                    filename: uploadedFile?.filename || file.name,
                  }
                : item
            )
          );
        } catch (error) {
          console.error(`Upload failed for ${file.name}:`, error);

          setAttachments((prev) =>
            prev.filter((item) => item.id !== attachmentId)
          );
        }
      }
    } finally {
      setUploading(false);
    }

    e.target.value = "";
  };

  const removeAttachment = (index) => {
    setAttachments((prev) =>
      prev.filter((_, i) => i !== index)
    );
  };

  const handleSend = () => {
    const trimmedText = text.trim();

    if (!trimmedText || uploading) return;

    const uploadedFiles = attachments
      .filter((item) => item.uploaded)
      .map((item) => item.file);

    onSend(trimmedText, uploadedFiles);

    setText("");
    setAttachments([]);
  };

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

  return (
    <div className="chat-input-container">

      {attachments.length > 0 && (
        <div className="attachment-list">
          {attachments.map((item, index) => (
            <div className="attachment-item" key={item.id}>
              <span className="attachment-icon">File</span>

              <div className="attachment-details">
                <span className="attachment-name">
                  {item.filename}
                </span>

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

                {item.uploaded && (
                  <span className="attachment-uploaded">
                    Uploaded
                  </span>
                )}
              </div>

              {item.uploaded && (
                <span className="attachment-check">
                  ✓
                </span>
              )}

              <button
                type="button"
                className="attachment-remove"
                onClick={() => removeAttachment(index)}
                title="Remove file"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="chat-input-shell">

        <div className="chat-input">

          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt"
            onChange={handleFileSelect}
            style={{ display: "none" }}
          />

          <button
            type="button"
            className="attach-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isStreaming || uploading}
            title="Attach file"
          >
            +
          </button>

          <textarea
            value={text}
            placeholder="Ask your AI Twin..."
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isStreaming}
            rows={1}
          />

          <div className="input-hint">
            <span>Enter to send</span>
            <span>Shift + Enter for new line</span>
          </div>

          {isStreaming ? (
            <button
              type="button"
              className="send-button stop-button"
              onClick={onStop}
              title="Stop generating"
            >
              <span className="stop-icon"></span>
            </button>
          ) : (
            <button
              type="button"
              className="send-button"
              onClick={handleSend}
              disabled={uploading || !text.trim()}
              title="Send message"
            >
              ↑
            </button>
          )}

        </div>

        <div className="input-status">
          <span className="input-status-dot"></span>
          AI Twin is ready
        </div>

      </div>
    </div>
  );
}

export default ChatInput;
