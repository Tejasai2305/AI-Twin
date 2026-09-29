import { useState } from "react";
import {
  signup,
  login,
  requestPasswordReset,
  setToken,
} from "../services/authApi";

function AuthGate({ onAuthenticated, onSkip }) {
  const [mode, setMode] = useState("login"); // "login" | "signup" | "forgot"
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const switchMode = (nextMode) => {
    setMode(nextMode);
    setError("");
    setSuccess("");
    setPassword("");
  };

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      if (mode === "forgot") {
        const res = await requestPasswordReset(email);
        setSuccess(res.data.message);
        return;
      }

      const res =
        mode === "login"
          ? await login(username, password)
          : await signup(username, password, email);

      setToken(res.data.access_token);
      onAuthenticated(res.data.user);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const isForgot = mode === "forgot";

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
          AI Twin
        </h1>

        <p style={{ color: "#aaa", marginBottom: "24px", fontSize: "14px" }}>
          {mode === "login"
            ? "Sign in to your AI Twin."
            : mode === "signup"
              ? "Create your AI Twin account."
              : "Reset your AI Twin password."}
        </p>

        <form onSubmit={submit}>
          {isForgot ? (
            <input
              type="email"
              placeholder="Email address"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "12px",
                marginBottom: "18px",
                borderRadius: "8px",
                border: "1px solid #555",
                background: "#40414f",
                color: "white",
                fontSize: "15px",
                boxSizing: "border-box",
              }}
            />
          ) : (
            <>
              <input
                type="text"
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                style={{
                  width: "100%",
                  padding: "12px",
                  marginBottom: "12px",
                  borderRadius: "8px",
                  border: "1px solid #555",
                  background: "#40414f",
                  color: "white",
                  fontSize: "15px",
                  boxSizing: "border-box",
                }}
              />

              {mode === "signup" && (
                <input
                  type="email"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  style={{
                    width: "100%",
                    padding: "12px",
                    marginBottom: "12px",
                    borderRadius: "8px",
                    border: "1px solid #555",
                    background: "#40414f",
                    color: "white",
                    fontSize: "15px",
                    boxSizing: "border-box",
                  }}
                />
              )}

              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                style={{
                  width: "100%",
                  padding: "12px",
                  marginBottom: "18px",
                  borderRadius: "8px",
                  border: "1px solid #555",
                  background: "#40414f",
                  color: "white",
                  fontSize: "15px",
                  boxSizing: "border-box",
                }}
              />
            </>
          )}

          {error && (
            <p
              style={{
                color: "#dc3545",
                fontSize: "13px",
                marginBottom: "14px",
              }}
            >
              {error}
            </p>
          )}

          {success && (
            <p
              style={{
                color: "#4ade80",
                fontSize: "13px",
                marginBottom: "14px",
              }}
            >
              {success}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px",
              borderRadius: "8px",
              border: "none",
              background: "#007bff",
              color: "white",
              fontSize: "15px",
              cursor: "pointer",
              marginBottom: "14px",
            }}
          >
            {loading
              ? "Please wait..."
              : mode === "login"
                ? "Sign In"
                : mode === "signup"
                  ? "Create Account"
                  : "Send Reset Link"}
          </button>
        </form>

        {mode === "login" && (
          <p style={{ textAlign: "center", fontSize: "13px", margin: "0 0 12px" }}>
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                switchMode("forgot");
              }}
              style={{ color: "#007bff" }}
            >
              Forgot password?
            </a>
          </p>
        )}

        <p style={{ textAlign: "center", fontSize: "13px", color: "#aaa" }}>
          {mode === "login" ? (
            <>
              Don't have an account?{" "}
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  switchMode("signup");
                }}
                style={{ color: "#007bff" }}
              >
                Sign up
              </a>
            </>
          ) : mode === "signup" ? (
            <>
              Already have an account?{" "}
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  switchMode("login");
                }}
                style={{ color: "#007bff" }}
              >
                Sign in
              </a>
            </>
          ) : (
            <>
              Remember your password?{" "}
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  switchMode("login");
                }}
                style={{ color: "#007bff" }}
              >
                Sign in
              </a>
            </>
          )}
        </p>

        {onSkip && mode !== "forgot" && (
          <p style={{ textAlign: "center", marginTop: "18px" }}>
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                onSkip();
              }}
              style={{ color: "#777", fontSize: "12px" }}
            >
              Continue without an account
            </a>
          </p>
        )}
      </div>
    </div>
  );
}

export default AuthGate;
