from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from ulid import ULID

from ..auth import get_owner_id
from ..db import get_db
from ..models import (
    SchemaCreate,
    SchemaOut,
    VersionCreate,
    VersionPatch,
    VersionOut,
    FormDefinition,
    AiChatRequest,
    AiChatResponse,
    AiApplyRequest,
)
from ..ai import run_ai_chat

router = APIRouter(prefix="/schemas", tags=["schemas"])


def _now():
    return datetime.now(timezone.utc)


def _schema_out(doc) -> SchemaOut:
    return SchemaOut(
        id=doc["id"],
        slug=doc["slug"],
        title=doc["title"],
        status=doc["status"],
        active_version=doc.get("active_version"),
        owner_id=doc.get("owner_id") or "anonymous",
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _require_owned_schema(db, schema_id: str, owner_id: str):
    """Return schema doc if owned by owner_id; 404 if missing or cross-owner."""
    schema = db.schemas.find_one({"id": schema_id}, {"_id": 0})
    if not schema:
        raise HTTPException(404, "schema not found")
    schema_owner = schema.get("owner_id") or "anonymous"
    if schema_owner != owner_id:
        raise HTTPException(403, "forbidden: schema owned by another owner")
    return schema
