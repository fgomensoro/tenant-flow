from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    postgres_user: str
    postgres_password: str
    postgres_app_password: str
    postgres_db: str
    postgres_port: int = 5432
    debug: bool = False
    admin_token: str

    @property
    def database_url(self) -> str:
        """For app runtime - uses NOSUPERUSER role."""
        return (
            f"postgresql+asyncpg://tenantflow_app:{self.postgres_app_password}"
            f"@localhost:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_admin(self) -> str:
        """For migrations and admin tasks - uses superuser."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@localhost:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
