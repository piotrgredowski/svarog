try:
    from ._version import version
except ImportError:  # pragma: no cover
    version = "unknown"

__version__ = version
