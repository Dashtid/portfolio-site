"""
Compression middleware for Gzip/Brotli response compression
"""

from starlette.middleware.gzip import DEFAULT_EXCLUDED_CONTENT_TYPES
from starlette.middleware.gzip import GZipMiddleware as StarletteGZipMiddleware

# PDFs gain 7-10% from gzip, and a FileResponse's 64 KB chunks are compressed
# on the event loop (Starlette sends only chunks of 128 KB and up to a
# thread): about 100 ms of CPU per 4 MB thesis, blocking every other request.
EXCLUDED_CONTENT_TYPES = (*DEFAULT_EXCLUDED_CONTENT_TYPES, "application/pdf")


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
        super().__init__(
            app, minimum_size=minimum_size, exclude_content_types=EXCLUDED_CONTENT_TYPES
        )
