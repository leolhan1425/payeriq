from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://payeriq:payeriq_dev@localhost:5432/payeriq"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ANTHROPIC_API_KEY: str = ""

    model_config = {"env_file": "../.env", "extra": "ignore"}


settings = Settings()
