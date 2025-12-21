from pydantic_settings import BaseSettings
from typing import List
import warnings


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
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.debug and self.secret_key == "dev-secret-key-change-in-production":
            warnings.warn(
                "SECURITY WARNING: You are using the default secret key in production! "
                "Please set a secure SECRET_KEY environment variable.",
                RuntimeWarning
            )


settings = Settings()