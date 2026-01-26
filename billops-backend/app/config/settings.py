from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "BillOps"
    environment: str = "development"
    database_url: str = "postgresql://user:password@localhost:5432/billops"
    jwt_secret: str = "change-me"
    session_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    redis_url: str = "redis://localhost:6379/0"
    redis_result_backend: str = "redis://localhost:6379/1"
    
    log_level: str = "INFO"

    # AWS / S3 configuration (optional)
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str | None = "us-east-1"
    s3_bucket_name: str | None = None
    s3_base_path: str | None = "invoices"

    # Google OAuth Configuration
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str | None = None  # e.g., "http://localhost:8000/api/v1/integrations/google/callback"
    
    # Microsoft OAuth Configuration
    microsoft_client_id: str | None = None
    microsoft_client_secret: str | None = None
    microsoft_tenant_id: str | None = None
    microsoft_redirect_uri: str | None = None  # e.g., "http://localhost:8000/api/v1/integrations/microsoft/callback"
    
    # Slack Configuration
    slack_bot_token: str | None = None
    slack_signing_secret: str | None = None
    slack_app_id: str | None = None
    slack_client_id: str | None = None
    slack_client_secret: str | None = None
    slack_redirect_uri: str | None = None
    
    # Email Configuration (SendGrid or SES)
    email_provider: str = "sendgrid"  # "sendgrid" or "ses"
    sendgrid_api_key: str | None = None
    ses_access_key_id: str | None = None
    ses_secret_access_key: str | None = None
    ses_region: str = "us-east-1"
    from_email: str = "noreply@billops.com"
    from_name: str = "BillOps"
    
    # Frontend URLs
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
