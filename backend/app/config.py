from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./optura.db"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # LLM
    openai_api_key: str = ""
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    
    # File Upload
    max_upload_size_mb: int = 10
    allowed_extensions: List[str] = [".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".md", ".txt", ".yaml", ".yml"]
    upload_dir: str = "./uploads"
    
    # Sandbox
    sandbox_timeout_seconds: int = 60
    sandbox_memory_limit_mb: int = 512
    
    # Debug
    debug: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()