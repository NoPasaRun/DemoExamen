from datetime import timedelta
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix='db_', extra="ignore")
    host: str = "localhost"
    port: int = 5432
    name: str = "postgres"
    user: str = "postgres"
    password: str = "postgres"
    echo: bool = False

    @property
    def url(self):
        return "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
            self.user, self.password, self.host, self.port, self.name
        )


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix='app_', extra="ignore")
    session_exp_time: timedelta = timedelta(seconds=3600 * 3)
    debug: bool = True
    salt: str = "secret"

    @property
    def root(self):
        return Path(__file__).parent.resolve()


app_settings = AppSettings()
db_settings = DBSettings()
