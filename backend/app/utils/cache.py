"""Redis cache utilities."""
import json
from typing import Optional, Any
import redis
from app.config import settings

# Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_cached(key: str) -> Optional[Any]:
    """Get value from cache."""
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None


async def set_cached(key: str, value: Any, ttl: int = None) -> bool:
    """Set value in cache with TTL."""
    try:
        ttl = ttl or settings.CACHE_TTL
        redis_client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        print(f"Cache set error: {e}")
        return False


async def delete_cached(key: str) -> bool:
    """Delete value from cache."""
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Cache delete error: {e}")
        return False


async def clear_user_cache(user_id: int) -> bool:
    """Clear all cached data for a user."""
    try:
        pattern = f"user:{user_id}:*"
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
        return True
    except Exception as e:
        print(f"Cache clear error: {e}")
        return False

