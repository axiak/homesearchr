import time

from google.appengine.api import memcache

from functools import wraps

CACHE_API_VERSION = '3'
CACHE_ADD_RO_TIME = 45 # 45 seconds 'till we run again
CACHE_ENABLE = True

def cacheview(keyfunc, cachetimeout=86400):
    if cachetimeout < 300:
        ro_time = None
    else:
        ro_time = int(min(600, cachetimeout * 0.05))
    def decorator(method):
        if not CACHE_ENABLE:
            return method

        @wraps(method)
        def _wrapper(*args, **kwargs):
            cache_key = keyfunc(*args, **kwargs)
            if cache_key is None:
                return method(*args, **kwargs)

            curtime = time.time()
            cache_key = version(cache_key)
            result = memcache.get(cache_key)
            if result:
                ro_timeout, result = result
                if ro_timeout < curtime:
                    return result

            ro_key = 'ro_' + cache_key
            if not memcache.add(ro_key, True, CACHE_ADD_RO_TIME):
                return result

            ro_timeout = curtime + ro_time
            result = method(*args, **kwargs)
            memcache.set(cache_key, (ro_timeout, result), time=cachetimeout)
            memcache.delete(ro_key)
            return result
        return _wrapper
    return decorator

def version(s):
    return '%s_%s' % (CACHE_API_VERSION, s)
