import sys

from itertools import chain
from collections import deque


def empty_profile(f):
    return f


# catch nameerror when mprof is not used
try:
    profile = profile
except NameError:
    profile = empty_profile


_HANDLERS = {
    tuple: iter,
    list: iter,
    deque: iter,
    set: iter,
    frozenset: iter,
    dict: lambda d: chain.from_iterable(d.items()),
}
_DEFAULT_SIZE = sys.getsizeof(0)  # estimate sizeof object without __sizeof__


def sizeof_fmt(num, suffix="B"):
    """ Returns human readable size of bytes. Adapted from
    https://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size"""
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}B"
        num /= 1024.0
    return f"{num:.1f} YiB"


def total_size(obj):
    """ Returns the approximate memory footprint an object and all of its contents.
    Adapted from https://code.activestate.com/recipes/577504/
    """
    seen = set()

    def sizeof(obj):
        if id(obj) in seen:
            return 0
        seen.add(id(obj))

        s = sys.getsizeof(obj, _DEFAULT_SIZE)

        for typ, handler in _HANDLERS.items():
            if isinstance(obj, typ):
                s += sum(map(sizeof, handler(obj)))
                break
        return s

    return sizeof_fmt(sizeof(obj))


__all__ = ["total_size", "sizeof_fmt"]
