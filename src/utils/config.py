import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    # For a real lambda deployment, we might want to get these from SSM Parameter Store or Secrets Manager
    # but for this implementation we will rely on env vars.

settings = Config()
