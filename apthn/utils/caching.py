import time
import logging

from google.appengine.api import memcache

from functools import wraps

CACHE_API_VERSION = '7'
CACHE_ADD_RO_TIME = 45 # 45 seconds 'till we run again
CACHE_ENABLE = True

def cacheview(keyfunc, cachetimeout=86400):
    if cachetimeout < 300:
        ro_time = None
    else:
        ro_time = int(max(cachetimeout - 600, cachetimeout * 0.95))
    def decorator(method):
        if not CACHE_ENABLE:
            return method

        @wraps(method)
        def _wrapper(*args, **kwargs):
            cache_key = keyfunc(*args, **kwargs)
            if cache_key is None:
                logging.info("CACHE: No cache")
                return method(*args, **kwargs)

            curtime = time.time()
            cache_key = version(cache_key)
            result = memcache.get(cache_key)
            if result:
                ro_timeout, result = result
                if ro_timeout < curtime:
                    logging.info("CACHE: HIT!")
                    return result
                else:
                    logging.info("CACHE: Hit but RO timeout")
            else:
                logging.info("CACHE: Miss")

            ro_key = 'ro_' + cache_key
            if result and not memcache.add(ro_key, True, CACHE_ADD_RO_TIME):
                logging.info("CACHE: RO timeout and someone else processing.")
                return result

            ro_timeout = curtime + ro_time
            result = method(*args, **kwargs)
            memcache.set(cache_key, (ro_timeout, result), time=cachetimeout)
            memcache.delete(ro_key)
            logging.info("CACHE: Set cache: %s (ro_time: %s)" % (cache_key, ro_timeout - curtime))
            return result
        return _wrapper
    return decorator

def version(s):
    return '%s_%s' % (CACHE_API_VERSION, s)
