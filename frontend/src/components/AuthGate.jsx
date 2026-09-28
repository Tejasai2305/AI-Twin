import { useState } from "react";
import { signup, login, setToken } from "../services/authApi";

function AuthGate({ onAuthenticated, onSkip }) {
  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = mode === "login"
        ? await login(username, password)
        : await signup(username, password);

      setToken(res.data.access_token);
      onAuthenticated(res.data.user);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#1e1f26",
      }}
    >
      <div
        style={{
          background: "#2f3136",
          padding: "40px",
          borderRadius: "12px",
          width: "360px",
          color: "white",
        }}
      >
        <h1 style={{ marginTop: 0, marginBottom: "6px", fontSize: "22px" }}>
          🧠 AI Twin
        </h1>
        <p style={{ color: "#aaa", marginBottom: "24px", fontSize: "14px" }}>
          {mode === "login" ? "Sign in to your AI Twin." : "Create your AI Twin account."}
        </p>

        <form onSubmit={submit}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{
              width: "100%", padding: "12px", marginBottom: "12px",
              borderRadius: "8px", border: "1px solid #555",
              background: "#40414f", color: "white", fontSize: "15px",
              boxSizing: "border-box",
            }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            style={{
              width: "100%", padding: "12px", marginBottom: "18px",
              borderRadius: "8px", border: "1px solid #555",
              background: "#40414f", color: "white", fontSize: "15px",
              boxSizing: "border-box",
            }}
          />

          {error && (
            <p style={{ color: "#dc3545", fontSize: "13px", marginBottom: "14px" }}>{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%", padding: "12px", borderRadius: "8px",
              border: "none", background: "#007bff", color: "white",
              fontSize: "15px", cursor: "pointer", marginBottom: "14px",
            }}
          >
            {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        <p style={{ textAlign: "center", fontSize: "13px", color: "#aaa" }}>
          {mode === "login" ? (
            <>Don't have an account?{" "}
              <a href="#" onClick={(e) => { e.preventDefault(); setMode("signup"); setError(""); }} style={{ color: "#007bff" }}>
                Sign up
              </a>
            </>
          ) : (
            <>Already have an account?{" "}
              <a href="#" onClick={(e) => { e.preventDefault(); setMode("login"); setError(""); }} style={{ color: "#007bff" }}>
                Sign in
              </a>
            </>
          )}
        </p>

        {onSkip && (
          <p style={{ textAlign: "center", marginTop: "18px" }}>
            <a href="#" onClick={(e) => { e.preventDefault(); onSkip(); }} style={{ color: "#777", fontSize: "12px" }}>
              Continue without an account
            </a>
          </p>
        )}
      </div>
    </div>
  );
}

export default AuthGate;
