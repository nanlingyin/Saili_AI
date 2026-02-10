import smtplib
from email.mime.text import MIMEText

from app.core.config import EMAIL_ENABLED, SMTP_FROM, SMTP_HOST, SMTP_PASSWORD, SMTP_PORT, SMTP_USER


def send_email(to_address: str, subject: str, body: str) -> None:
    if not EMAIL_ENABLED:
        raise RuntimeError("email not configured")

    message = MIMEText(body, _charset="utf-8")
    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = to_address

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, [to_address], message.as_string())