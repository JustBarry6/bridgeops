from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str
    redis_url: str
    azure_storage_connection_string: str = "UseDevelopmentStorage=true"
    jwt_secret_key: str = "change-me"
    fernet_key: str = "change-me"
    simulate_failure: bool = False


settings = Settings()