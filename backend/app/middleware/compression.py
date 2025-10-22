"""
Compression middleware for Gzip/Brotli response compression
"""
from starlette.middleware.gzip import GZipMiddleware as StarletteGZipMiddleware


class CompressionMiddleware(StarletteGZipMiddleware):
    """
    Gzip compression middleware

    Compresses responses larger than minimum_size bytes (default 1KB)
    Automatically adds Content-Encoding header
    """

    def __init__(self, app, minimum_size: int = 1000):
        """
        Initialize compression middleware

        Args:
            app: ASGI application
            minimum_size: Minimum response size in bytes to compress (default 1KB)
        """
        super().__init__(app, minimum_size=minimum_size)
