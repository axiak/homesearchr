from google.appengine.api import memcache

from functools import wraps

def cacheview(keyfunc, time=86400):
    def decorator(method):
        @wraps(method)
        def _wrapper(*args, **kwargs):
            cache_key = keyfunc(*args, **kwargs)
            if cache_key is None:
                return method(*args, **kwargs)
            result = memcache.get(cache_key)
            if result:
                return result
            result = method(*args, **kwargs)
            memcache.set(cache_key, result, time=time)
            return result
        return _wrapper
    return decorator