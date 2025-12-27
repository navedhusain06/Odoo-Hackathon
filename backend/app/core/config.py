from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_name: str = "GearGuard API"

    postgres_db: str = "gearguard"
    postgres_user: str = "gearguard"
    postgres_password: str = "gearguard"
    postgres_host: str = "db"
    postgres_port: int = 5432


settings = Settings()
