import { useState } from "react";
import { resetPassword } from "../services/authApi";

function ResetPassword() {
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const token = new URLSearchParams(window.location.search).get("token");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!token) {
      setError("This password reset link is invalid.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const res = await resetPassword(token, password);
      setSuccess(res.data.message);
      setPassword("");
      setConfirmPassword("");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || "Unable to reset your password.");
    } finally {
      setLoading(false);
    }
  };

  const goToLogin = () => {
    window.history.replaceState({}, "", "/");
    window.location.reload();
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
        <h1
          style={{
            marginTop: 0,
            marginBottom: "6px",
            fontSize: "22px",
          }}
        >
          AI Twin
        </h1>

        <p
          style={{
            color: "#aaa",
            marginBottom: "24px",
            fontSize: "14px",
          }}
        >
          Create a new password for your account.
        </p>

        <form onSubmit={submit}>
          <input
            type="password"
            placeholder="New password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
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

          <input
            type="password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
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

          {!success && (
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
              {loading ? "Resetting..." : "Reset Password"}
            </button>
          )}
        </form>

        {success && (
          <button
            type="button"
            onClick={goToLogin}
            style={{
              width: "100%",
              padding: "12px",
              borderRadius: "8px",
              border: "none",
              background: "#007bff",
              color: "white",
              fontSize: "15px",
              cursor: "pointer",
            }}
          >
            Back to Sign In
          </button>
        )}
      </div>
    </div>
  );
}

export default ResetPassword;
