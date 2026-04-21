from pydantic_settings import BaseSettings
from typing import Optional
import json

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Assisted Teaching System"
    API_V1_STR: str = "/api/v1"
    
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "db"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "app"
    DATABASE_URL: Optional[str] = None

    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_CHAT_MODEL: Optional[str] = None
    LLM_FALLBACK_CHAT_MODEL: Optional[str] = None
    LLM_EMBEDDING_MODEL: Optional[str] = "text-embedding-3-small"
    EMBEDDING_PROVIDER: str = "auto"
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_BASE_URL: Optional[str] = None
    RAG_RETRIEVE_TOP_K: int = 3

    SECRET_KEY: str = "changethis"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    BACKEND_CORS_ORIGINS: Optional[str] = ""

    class Config:
        case_sensitive = True
        env_file = ".env"

    def get_database_url(self):
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_cors_origins(self) -> list[str]:
        raw = (self.BACKEND_CORS_ORIGINS or "").strip()
        if not raw:
            return []

        if raw.startswith("["):
            try:
                values = json.loads(raw)
                if isinstance(values, list):
                    return [str(v).strip() for v in values if str(v).strip()]
            except json.JSONDecodeError:
                pass

        return [item.strip() for item in raw.split(",") if item.strip()]

settings = Settings()
