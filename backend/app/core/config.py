from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "GearGuard API"

    postgres_db: str = "gearguard"
    postgres_user: str = "gearguard"
    postgres_password: str = "gearguard"
    postgres_host: str = "db"
    postgres_port: int = 5432

    jwt_secret: str = "dev-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_exp_minutes: int = 60 * 24

    cors_origins: str = "http://localhost:3000,http://frontend:3000"


settings = Settings()
