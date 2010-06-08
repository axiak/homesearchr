import random
import string

__all__ = ('randstr',)

def randstr(n=10):
    return ''.join(random.choice(string.lowercase) for x in range(n))
