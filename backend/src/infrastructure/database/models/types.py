"""Custom SQLAlchemy types for the infrastructure layer."""

from __future__ import annotations

import zlib
from typing import Optional

from sqlalchemy.types import TypeDecorator, LargeBinary


class CompressedText(TypeDecorator):
    """Store text compressed (zlib) in the DB and transparently decompress on read.

    Uses LargeBinary as the underlying impl. This keeps DB size smaller for
    article bodies stored in the `articles` table.
    """

    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: Optional[str], dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return zlib.compress(value.encode("utf-8"))
        raise TypeError("CompressedText only accepts str or None")

    def process_result_value(self, value: Optional[bytes], dialect):
        if value is None:
            return None
        try:
            return zlib.decompress(value).decode("utf-8")
        except Exception:
            # If decompression fails, return raw bytes decoded as latin-1 to avoid crashes
            return value.decode("latin-1")
