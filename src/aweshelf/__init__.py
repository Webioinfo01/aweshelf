"""aweshelf package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("aweshelf")
except PackageNotFoundError:
    __version__ = "0.0.0"  # fallback for running from source without install
