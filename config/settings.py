# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Variables de la Base de Datos
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str = "customer_service"
    PROXY_PORT: int = 5433
    DB_ROOT_PASSWORD: str
    DB_CONNECTION_NAME: str
    DB_HOST: str

    # Credenciales de GCP 
    GCP_PROJECT_ID: str = "customer-service-agents-tfm"
    GOOGLE_API_KEY: str  

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()