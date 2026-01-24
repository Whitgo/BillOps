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

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
