import redis
import json
import os
from loguru import logger

redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"),
    decode_responses=True
)

def get_cache(key: str):
    """Get a value from cache"""
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.warning(f"Cache GET failed for key '{key}': {e}")
        return None

def set_cache(key: str, value, expire_seconds: int = 300):
    """Store a value in cache (default: 5 minutes)"""
    try:
        redis_client.setex(key, expire_seconds, json.dumps(value))
    except Exception as e:
        logger.warning(f"Cache SET failed for key '{key}': {e}")

def delete_cache(key: str):
    """Remove a value from cache"""
    try:
        redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Cache DELETE failed for key '{key}': {e}")

def delete_pattern(pattern: str):
    """Remove all keys matching a pattern"""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache DELETE pattern failed for '{pattern}': {e}")