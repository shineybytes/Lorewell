from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str
    openai_model: str = "gpt-5.4-mini"
    page_access_token: str
    instagram_account_id: str
    graph_api_version: str = "v25.0"
    app_base_url: str = "http://localhost:8000"
    media_dir: str = "media"
    database_url: str = "sqlite:///./lorewell.db"
    default_brand_voice: str = "elegant, warm, story-driven, clear call to action"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
