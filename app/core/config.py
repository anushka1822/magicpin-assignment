from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    LLM_PROVIDER: str
    LLM_API_KEY: str
    ENVIRONMENT: str = "development"
    PORT: int = 8080

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
