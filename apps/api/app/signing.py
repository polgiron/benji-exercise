"""Standard Webhooks signing (https://www.standardwebhooks.com/).

Headers on every delivery:
    webhook-id         stable across retries and replays, so receivers can dedupe
    webhook-timestamp  unix seconds of this attempt
    webhook-signature  "v1,<base64 HMAC-SHA256(key, f'{id}.{timestamp}.{body}')>"

The timestamp is part of the signed content, so a captured request can't be replayed
outside the tolerance window. This module has no FastAPI imports: `verify()` is the
snippet we'd hand customers.
"""

import base64
import hashlib
import hmac
import secrets
import time
from collections.abc import Mapping

SECRET_PREFIX = "whsec_"


class InvalidSignature(Exception):
    pass


def generate_secret() -> str:
    return SECRET_PREFIX + base64.b64encode(secrets.token_bytes(32)).decode()


def _key(secret: str) -> bytes:
    return base64.b64decode(secret.removeprefix(SECRET_PREFIX))


def sign(secret: str, msg_id: str, timestamp: int, body: bytes) -> str:
    signed = f"{msg_id}.{timestamp}.".encode() + body
    digest = hmac.new(_key(secret), signed, hashlib.sha256).digest()
    return "v1," + base64.b64encode(digest).decode()


def signature_headers(secret: str, msg_id: str, body: bytes, timestamp: int) -> dict[str, str]:
    return {
        "webhook-id": msg_id,
        "webhook-timestamp": str(timestamp),
        "webhook-signature": sign(secret, msg_id, timestamp, body),
    }


def verify(
    secret: str,
    headers: Mapping[str, str],
    body: bytes,
    tolerance: int = 300,
    now: float | None = None,
) -> None:
    """Raise InvalidSignature unless `body` was signed with `secret` within `tolerance` s.

    Pass the RAW request body, before any JSON parsing: re-serialising changes the bytes.
    """
    msg_id = headers.get("webhook-id")
    ts_header = headers.get("webhook-timestamp")
    sig_header = headers.get("webhook-signature")
    if not (msg_id and ts_header and sig_header):
        raise InvalidSignature("missing webhook headers")
    try:
        timestamp = int(ts_header)
    except ValueError:
        raise InvalidSignature("invalid timestamp") from None
    now = time.time() if now is None else now
    if abs(now - timestamp) > tolerance:
        raise InvalidSignature("timestamp outside tolerance")

    expected = sign(secret, msg_id, timestamp, body)
    # The header may carry several space-separated signatures (secret rotation).
    if not any(hmac.compare_digest(expected, s) for s in sig_header.split()):
        raise InvalidSignature("no matching signature")
