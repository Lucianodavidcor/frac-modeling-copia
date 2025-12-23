import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Interference-Sim-API")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    
    # Leemos la URL y si viene como 'postgres://', la reemplazamos por 'postgresql://'
    _database_url: str = os.getenv("DATABASE_URL")
    
    @property
    def DATABASE_URL(self):
        if self._database_url and self._database_url.startswith("postgres://"):
            return self._database_url.replace("postgres://", "postgresql://", 1)
        return self._database_url

settings = Settings()