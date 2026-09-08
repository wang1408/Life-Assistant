from email.message import EmailMessage
import smtplib
from app.core.config import get_settings


class SMTPClient:
    def send(self, to: str, subject: str, body: str) -> None:
        settings = get_settings()
        if not settings.smtp_host or not settings.smtp_from:
            raise RuntimeError("SMTP 未配置")
        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        smtp_cls = smtplib.SMTP_SSL if settings.smtp_port == 465 else smtplib.SMTP
        with smtp_cls(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_port != 465:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
