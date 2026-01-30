import hashlib
import redis
import json
from src.utils.config import settings

# Initialize Redis client
r = redis.from_url(settings.REDIS_URL, decode_responses=True)

def get_content_hash(content: bytes) -> str:
    """
    Computes SHA256 hash of the content.
    """
    return hashlib.sha256(content).hexdigest()

def get_cached_summary(file_hash: str) -> str:
    """
    Retrieves cached summary by file hash.
    """
    try:
        return r.get(f"summary:{file_hash}")
    except redis.RedisError:
        return None

def cache_summary(file_hash: str, summary: str, ttl: int = 86400):
    """
    Caches the summary with a TTL (default 24 hours).
    """
    try:
        r.setex(f"summary:{file_hash}", ttl, summary)
    except redis.RedisError:
        pass
