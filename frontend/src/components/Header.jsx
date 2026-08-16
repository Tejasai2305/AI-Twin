import "./Header.css";

function Header() {
  return (
    <div className="header">
      <div className="header-left">
        <h2>AI Twin</h2>
      </div>

      <div className="header-right">
        <span className="model">Gemini 3.1 Flash Lite</span>
      </div>
    </div>
  );
}

export default Header;