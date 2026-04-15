import logging
import smtplib
from email.message import EmailMessage

import requests

from app.config import settings


LOGGER = logging.getLogger(__name__)


def send_digest_email(to_email: str, subject: str, html_body: str, text_body: str) -> None:
    if settings.sendgrid_api_key:
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": settings.sendgrid_from or settings.smtp_from},
            "subject": subject,
            "content": [
                {"type": "text/plain", "value": text_body},
                {"type": "text/html", "value": html_body},
            ],
        }
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.sendgrid_api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        LOGGER.info("Sent SendGrid digest email to %s", to_email)
        return

    message = EmailMessage()
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.starttls()
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
    LOGGER.info("Sent SMTP digest email to %s", to_email)
