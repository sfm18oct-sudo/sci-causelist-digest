from pydantic import BaseModel
import os


class Settings(BaseModel):
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://sci:sci@localhost:5432/sci_digest")
    secret_key: str = os.getenv("APP_SECRET_KEY", "dev-secret")
    timezone: str = os.getenv("APP_TIMEZONE", "Asia/Kolkata")
    mode: str = os.getenv("APP_MODE", "A")
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "apikey")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from: str = os.getenv("SMTP_FROM", "noreply@example.com")
    sendgrid_api_key: str = os.getenv("SENDGRID_API_KEY", "")
    sendgrid_from: str = os.getenv("SENDGRID_FROM", "")


settings = Settings()
