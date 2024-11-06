from time import time
from functools import wraps

def time_benchmark(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        ts = time()
        result = f(*args, **kwargs)
        te = time()
        print('func:%s took: %2.4f sec' % (f.__name__, te-ts))

        return result
    return wrap