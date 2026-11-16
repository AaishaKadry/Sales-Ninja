from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Sales Ninja API"
    database_url: str = "sqlite:///./sales_ninja.db"
    aws_region: str = "ap-south-1"
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    aws_profile: str | None = None
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_mb: int = 10
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
