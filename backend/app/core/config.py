import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", 24))
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

settings = Settings()