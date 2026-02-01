from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):


    # Application
    app_name: str = "Watch Party"
    environment: str = "development"
    debug: bool = False

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    backend_cors_origins: list[str] = ["http://localhost:5173"]

    # Room Settings
    max_room_participants: int = 6
    room_timeout_hours: int = 4

    # API
    api_v1_prefix: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )



settings = Settings()
