"""
k3thread is utility to create and operate thread.

Start a daemon thread after 0.2 seconds::

    >>> th = daemon(lambda :1, after=0.2)

Stop a thread by sending a exception::

    import time

    def busy():
        while True:
            time.sleep(0.1)

    t = daemon(busy)
    send_exception(t, SystemExit)

"""

from .thd import InvalidThreadIdError, SendRaiseError, daemon, send_exception, start

__all__ = [
    "InvalidThreadIdError",
    "SendRaiseError",
    "daemon",
    "send_exception",
    "start",
]


def __getattr__(name: str) -> str:
    # importlib.metadata takes about 20 ms to import, so it is loaded only
    # when __version__ is read
    if name != "__version__":
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from importlib.metadata import version

    return version("k3thread")
