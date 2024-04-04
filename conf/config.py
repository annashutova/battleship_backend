from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BIND_IP: str
    BIND_PORT: str
    DB_URL: str

    JWT_SECRET_SALT: str

    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_BATTLESHIP_CACHE_PREFIX: str = 'battleship'

    LOG_LEVEL: str = 'debug'


settings = Settings()
