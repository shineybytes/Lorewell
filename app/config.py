from pydantic_settings import BaseSettings, SettingsConfigDict
import os


def get_env_file() -> str:
    if os.getenv("PYTEST_RUNNING") == "1":
        return ".env.test"
    return ".env"


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str
    page_access_token: str
    instagram_account_id: str
    graph_api_version: str = "v25.0"
    app_base_url: str
    media_dir: str
    database_url: str
    default_brand_voice: str

    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        extra="ignore",
    )


settings = Settings()
