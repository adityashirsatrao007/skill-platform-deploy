import redis
import json
import os


class CacheService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                cls._instance.client = redis.from_url(redis_url, decode_responses=True)
                cls._instance.client.ping()
                cls._instance._available = True
                print("Redis connected")
            except Exception:
                cls._instance._available = False
                print("Redis unavailable, caching disabled")
        return cls._instance

    def get(self, key):
        if not self._available:
            return None
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    def set(self, key, value, ttl=300):
        if not self._available:
            return
        try:
            self.client.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            pass

    def delete(self, key):
        if not self._available:
            return
        try:
            self.client.delete(key)
        except Exception:
            pass
