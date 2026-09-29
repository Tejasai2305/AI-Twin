import os

import resend


def send_password_reset_email(email: str, reset_url: str):
    api_key = os.getenv("RESEND_API_KEY")
    from_email = os.getenv("RESEND_FROM_EMAIL")

    if not api_key:
        raise RuntimeError("RESEND_API_KEY is not configured.")

    if not from_email:
        raise RuntimeError("RESEND_FROM_EMAIL is not configured.")

    resend.api_key = api_key

    resend.Emails.send(
        {
            "from": from_email,
            "to": [email],
            "subject": "Reset your AI Twin password",
            "html": f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
                <h2>Reset your AI Twin password</h2>
                <p>We received a request to reset your AI Twin password.</p>
                <p>
                    <a href="{reset_url}"
                       style="display:inline-block;padding:12px 20px;
                              background:#007bff;color:white;
                              text-decoration:none;border-radius:6px;">
                        Reset Password
                    </a>
                </p>
                <p>This link expires in 30 minutes and can only be used once.</p>
                <p>If you did not request a password reset, you can safely ignore this email.</p>
            </div>
            """,
        }
    )
