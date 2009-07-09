import threading
import time

class Unblocker(threading.Thread):
    """Release `lock` after `t` seconds.

    """
    def __init__(self, lock, t):
        self.lock = lock
        self.time = t
        super(Unblocker, self).__init__()

    def run(self):
        try:
            time.sleep(self.time)
        finally:
            self.lock.release()

def call_interval(t):
    """Make sure that the decorated function won't be called again for
    at least `t` seconds, after each call.

    This is useful if you for example have a limit of maximum _n_
    calls to an API per second and you want to be on the safe side
    that you won't exceed it.

    """
    def decorator(fun):
        d = threading.Lock()
        def _wrapper(*a, **kw):
            d.acquire()
            u = Unblocker(d, t)
            try:
                return fun(*a, **kw)
            finally:
                u.start()
        return _wrapper
    return decorator
