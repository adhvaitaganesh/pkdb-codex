from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PKDB_")

    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "pkdb"


settings = Settings()
