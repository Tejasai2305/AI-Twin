import "./Header.css";

function Header({ currentUser, onLogout, isStreaming }) {
  return (
    <div className="header">
      <div className="header-left">
        <div className={`header-twin-core ${isStreaming ? "header-twin-thinking" : ""}`}>
          <span>AI</span>
        </div>

        <div className="header-twin-info">
          <h2>AI Twin</h2>
          <span>
            <i className="header-status-dot"></i>
            {isStreaming ? "Thinking..." : "Online"}
          </span>
        </div>
      </div>

      <div className="header-right">
        <span className="model">Gemini 3.1 Flash Lite</span>        <span className="header-user">
          {currentUser ? currentUser.username : "Local Mode"}

          {onLogout && (
            <button onClick={onLogout}>
              Log out
            </button>
          )}
        </span>
      </div>
    </div>
  );
}

export default Header;

