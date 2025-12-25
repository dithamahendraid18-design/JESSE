from __future__ import annotations

import logging
import sys
import uuid
from flask import g, request


def setup_logging() -> None:
    """
    Logging standar production:
    - output ke stdout (bagus untuk Docker)
    - format simpel tapi informatif
    """
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def attach_request_id() -> None:
    """
    Set request_id untuk tracing.
    Bisa kamu pakai saat debug issue dari client tertentu.
    """
    g.request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())


def log_request() -> None:
    """
    Log ringkas per request.
    """
    logger = logging.getLogger("jesse")
    logger.info(
        "request_id=%s method=%s path=%s client_ip=%s",
        getattr(g, "request_id", "-"),
        request.method,
        request.path,
        request.remote_addr,
    )
