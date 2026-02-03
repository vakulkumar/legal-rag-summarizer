import os
import logging
from dotenv import load_dotenv
from src.utils.secrets import get_secret

load_dotenv()
logger = logging.getLogger(__name__)

class Config:
    def __init__(self):
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "legal-rag-documents")
        self.AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

        # Secrets Management
        self.OPENAI_API_KEY = self._get_openai_api_key()

    def _get_openai_api_key(self):
        # First check if explicit key env var is set
        key = os.getenv("OPENAI_API_KEY")
        # If key looks like a real key (sk-...), use it.
        # If it looks like an ARN or is empty, try secret.
        # But user might put ARN in OPENAI_API_KEY env var by mistake?
        # Let's rely on OPENAI_API_SECRET_ARN.

        secret_arn = os.getenv("OPENAI_API_SECRET_ARN")
        if secret_arn:
            try:
                logger.info("Fetching OpenAI API Key from Secrets Manager")
                return get_secret(secret_arn, self.AWS_REGION)
            except Exception as e:
                logger.warning(f"Could not fetch secret from ARN: {e}")
                # Fallback to key if present
                if key:
                     return key
                raise e

        return key

settings = Config()
