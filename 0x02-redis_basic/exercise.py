
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
        '''Stores a value in a Redis data storage and returns the key.
        '''
        data_key = str(uuid.uuid4())
        self._redis.set(data_key, data)
        return data_key

    def get(
            self,
            key: str,
            fn: Callable = None,
            ) -> Union[str, bytes, int, float]:
        '''Retrieves a value from a Redis data storage.
        '''
        data = self._redis.get(key)
        return fn(data) if fn is not None else data

    def get_str(self, key: str) -> str:
        '''Retrieves a string value from a Redis data storage.
        '''
        return self.get(key, lambda x: x.decode('utf-8'))

    def get_int(self, key: str) -> int:
        '''Retrieves an integer value from a Redis data storage.
        '''
        return self.get(key, lambda x: int(x))
