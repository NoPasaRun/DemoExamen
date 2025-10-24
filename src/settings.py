from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix='db_')
    host: str = "localhost"
    port: int = 5432
    name: str = "postgres"
    user: str = "postgres"
    password: str = "postgres"
    echo: bool = False

    @property
    def url(self):
        return "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
            self.name, self.password, self.host, self.port, self.name
        )


db_settings = DBSettings()
