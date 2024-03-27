
#!/usr/bin/env python3
"""
Writing strings to redis
"""
from typing import Union, Callable
from functools import wraps
import redis
import uuid


def call_history(method: Callable) -> Callable:
    @wraps(method)
    def wrapper(self, *args, **kwds):
        inKey = method.__qualname__ + ":inputs"
        outKey = method.__qualname__ + ":outputs"
        self._redis.rpush(inKey, str(args))
        output = method(self, *args, **kwds)
        self._redis.rpush(outKey, str(output))
        return output
    return wrapper


def count_calls(method: Callable) -> Callable:
    @wraps(method)
    def wrapper(self, *args, **kwds):
        self._redis.incr(method.__qualname__)
        if method is not None:
            return method(self, *args, **kwds)
    return wrapper


class Cache:
    def __init__(self) -> None:
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        key = uuid.uuid1()
        self._redis.set(str(key), data)
        return str(key)

    def get(self, key: str, fn: Callable = None):
        """get key from redis database"""
        if fn is not None:
            return fn(self._redis.get(key))
        return self._redis.get(key)

    def get_str(self, key: str) -> str:
        """convert binary to string"""
        return self._redis.get(key).decode("utf-8")

    def get_int(self, key: str) -> int:
        """convert binary to string then to int"""
        return int(self._redis.get(key).decode("utf-8"))
