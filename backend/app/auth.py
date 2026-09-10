"""Simple demo owner auth: Bearer token or X-Owner-Id.

APP should always send Authorization: Bearer <token>.
If missing, owner_id defaults to ``anonymous`` (local/curl convenience only).
owner_id is the raw token string (or X-Owner-Id value) — no JWT verification in this demo.
"""
from __future__ import annotations

from fastapi import Header


DEFAULT_OWNER_ID = "anonymous"


def get_owner_id(
    authorization: str | None = Header(default=None),
    x_owner_id: str | None = Header(default=None, alias="X-Owner-Id"),
) -> str:
    """Derive owner_id from Bearer token or X-Owner-Id; else anonymous."""
    if authorization:
        parts = authorization.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
            if token:
                return token
    if x_owner_id and x_owner_id.strip():
        return x_owner_id.strip()
    return DEFAULT_OWNER_ID
