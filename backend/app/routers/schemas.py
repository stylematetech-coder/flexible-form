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


def _version_out(doc) -> VersionOut:
    return VersionOut(
        id=doc["id"],
        schema_id=doc["schema_id"],
        version=doc["version"],
        status=doc["status"],
        definition=FormDefinition.model_validate(doc["definition"]),
        created_at=doc["created_at"],
        published_at=doc.get("published_at"),
        preview_token=doc.get("preview_token"),
    )


@router.post("", response_model=SchemaOut)
def create_schema(body: SchemaCreate, owner_id: str = Depends(get_owner_id)):
    db = get_db()
    if db.schemas.find_one({"slug": body.slug}):
        raise HTTPException(400, "slug already exists")
    now = _now()
    schema_id = str(ULID())
    schema_doc = {
        "id": schema_id,
        "slug": body.slug,
        "title": body.title,
        "status": "draft",
        "active_version": None,
        "owner_id": owner_id,
        "created_at": now,
        "updated_at": now,
    }
    db.schemas.insert_one(schema_doc)

    version_id = str(ULID())
    version_doc = {
        "id": version_id,
        "schema_id": schema_id,
        "version": 1,
        "status": "draft",
        "definition": FormDefinition().model_dump(),
        "created_at": now,
        "published_at": None,
        "preview_token": None,
    }
    db.schema_versions.insert_one(version_doc)
    return _schema_out(schema_doc)


@router.get("", response_model=list[SchemaOut])
def list_schemas(owner_id: str = Depends(get_owner_id)):
    db = get_db()
    docs = list(
        db.schemas.find({"owner_id": owner_id}, {"_id": 0}).sort("updated_at", -1)
    )
    return [_schema_out(d) for d in docs]


@router.get("/{schema_id}")
def get_schema(schema_id: str, owner_id: str = Depends(get_owner_id)):
    db = get_db()
    schema = _require_owned_schema(db, schema_id, owner_id)
    versions = list(
        db.schema_versions.find({"schema_id": schema_id}, {"_id": 0}).sort("version", -1)
    )
    return {
        "schema": _schema_out(schema),
        "versions": [_version_out(v) for v in versions],
    }


@router.post("/{schema_id}/versions", response_model=VersionOut)
def create_version(
    schema_id: str,
    body: VersionCreate | None = None,
    owner_id: str = Depends(get_owner_id),
):
    if body is None:
        body = VersionCreate()
    db = get_db()
    schema = _require_owned_schema(db, schema_id, owner_id)

    existing_draft = db.schema_versions.find_one(
        {"schema_id": schema_id, "status": "draft"}
    )
    if existing_draft:
        raise HTTPException(400, "draft version already exists")

    last = db.schema_versions.find_one(
        {"schema_id": schema_id}, sort=[("version", -1)]
    )
    next_ver = (last["version"] if last else 0) + 1

    if body.definition:
        definition = body.definition.model_dump()
    elif last:
        definition = last["definition"]
    else:
        definition = FormDefinition().model_dump()

    now = _now()
    doc = {
        "id": str(ULID()),
        "schema_id": schema_id,
        "version": next_ver,
        "status": "draft",
        "definition": definition,
        "created_at": now,
        "published_at": None,
        "preview_token": None,
    }
    db.schema_versions.insert_one(doc)
    db.schemas.update_one(
        {"id": schema_id},
        {"$set": {"updated_at": now, "status": "draft"}},
    )
    return _version_out(doc)


@router.patch("/{schema_id}/versions/{vid}", response_model=VersionOut)
def patch_version(
    schema_id: str, vid: str, body: VersionPatch, owner_id: str = Depends(get_owner_id)
):
    db = get_db()
    _require_owned_schema(db, schema_id, owner_id)
    ver = db.schema_versions.find_one({"id": vid, "schema_id": schema_id})
    if not ver:
        raise HTTPException(404, "version not found")
    if ver["status"] != "draft":
        raise HTTPException(400, "only draft versions can be edited")

    now = _now()
    db.schema_versions.update_one(
        {"id": vid},
        {"$set": {"definition": body.definition.model_dump()}},
    )
    db.schemas.update_one({"id": schema_id}, {"$set": {"updated_at": now}})
    ver = db.schema_versions.find_one({"id": vid}, {"_id": 0})
    return _version_out(ver)


@router.post("/{schema_id}/versions/{vid}/preview", response_model=VersionOut)
def preview_version(schema_id: str, vid: str, owner_id: str = Depends(get_owner_id)):
    db = get_db()
    _require_owned_schema(db, schema_id, owner_id)
    ver = db.schema_versions.find_one({"id": vid, "schema_id": schema_id})
    if not ver:
        raise HTTPException(404, "version not found")
    if ver["status"] not in ("draft", "preview"):
        raise HTTPException(400, "only draft/preview can be previewed")

    token = ver.get("preview_token") or str(ULID())
    db.schema_versions.update_one(
        {"id": vid},
        {"$set": {"status": "preview", "preview_token": token}},
    )
    ver = db.schema_versions.find_one({"id": vid}, {"_id": 0})
    return _version_out(ver)


@router.post("/{schema_id}/versions/{vid}/publish", response_model=VersionOut)
def publish_version(schema_id: str, vid: str, owner_id: str = Depends(get_owner_id)):
    db = get_db()
    _require_owned_schema(db, schema_id, owner_id)
    ver = db.schema_versions.find_one({"id": vid, "schema_id": schema_id})
    if not ver:
        raise HTTPException(404, "version not found")
    if ver["status"] == "published":
        raise HTTPException(400, "already published (immutable)")

    now = _now()
    db.schema_versions.update_one(
        {"id": vid},
        {"$set": {"status": "published", "published_at": now}},
    )
    db.schemas.update_one(
        {"id": schema_id},
        {"$set": {"active_version": ver["version"], "status": "published", "updated_at": now}},
    )
    ver = db.schema_versions.find_one({"id": vid}, {"_id": 0})
    return _version_out(ver)


@router.post("/{schema_id}/versions/{vid}/rollback", response_model=VersionOut)
def rollback_version(schema_id: str, vid: str, owner_id: str = Depends(get_owner_id)):
    """Rollback = re-publish older version as new published version."""
    db = get_db()
    schema = _require_owned_schema(db, schema_id, owner_id)

    old = db.schema_versions.find_one({"id": vid, "schema_id": schema_id})
    if not old:
        raise HTTPException(404, "version not found")
    if old["status"] != "published":
        raise HTTPException(400, "can only rollback to a published version")

    db.schema_versions.delete_many({"schema_id": schema_id, "status": "draft"})

    last = db.schema_versions.find_one(
        {"schema_id": schema_id}, sort=[("version", -1)]
    )
    next_ver = (last["version"] if last else 0) + 1
    now = _now()
    new_doc = {
        "id": str(ULID()),
        "schema_id": schema_id,
        "version": next_ver,
        "status": "published",
        "definition": old["definition"],
        "created_at": now,
        "published_at": now,
        "preview_token": None,
    }
    db.schema_versions.insert_one(new_doc)
    db.schemas.update_one(
        {"id": schema_id},
        {"$set": {"active_version": next_ver, "status": "published", "updated_at": now}},
    )
    return _version_out(new_doc)


def _ensure_draft(db, schema_id: str):
    """Return current draft version doc, creating one from latest if needed."""
    draft = db.schema_versions.find_one({"schema_id": schema_id, "status": "draft"})
    if draft:
        return draft
    preview = db.schema_versions.find_one(
        {"schema_id": schema_id, "status": "preview"}, sort=[("version", -1)]
    )
    if preview:
        db.schema_versions.update_one(
            {"id": preview["id"]},
            {"$set": {"status": "draft"}},
        )
        return db.schema_versions.find_one({"id": preview["id"]})

    last = db.schema_versions.find_one(
        {"schema_id": schema_id}, sort=[("version", -1)]
    )
    if not last:
        raise HTTPException(404, "no versions found")
    if last["status"] == "draft":
        return last

    next_ver = last["version"] + 1
    now = _now()
    doc = {
        "id": str(ULID()),
        "schema_id": schema_id,
        "version": next_ver,
        "status": "draft",
        "definition": last["definition"],
        "created_at": now,
        "published_at": None,
        "preview_token": None,
    }
    db.schema_versions.insert_one(doc)
    db.schemas.update_one(
        {"id": schema_id},
        {"$set": {"updated_at": now, "status": "draft"}},
    )
    return doc


@router.post("/{schema_id}/ai/chat", response_model=AiChatResponse)
def ai_chat(schema_id: str, body: AiChatRequest, owner_id: str = Depends(get_owner_id)):
    db = get_db()
    schema = _require_owned_schema(db, schema_id, owner_id)

    draft = _ensure_draft(db, schema_id)
    definition = draft["definition"]
    messages = [{"role": m.role, "content": m.content} for m in body.messages]
    reply, proposed, new_title = run_ai_chat(
        definition, messages, schema_title=schema.get("title")
    )
    return AiChatResponse(
        reply=reply,
        proposed_definition=proposed,
        proposed_schema_title=new_title,
    )


@router.post("/{schema_id}/ai/apply", response_model=VersionOut)
def ai_apply(schema_id: str, body: AiApplyRequest, owner_id: str = Depends(get_owner_id)):
    db = get_db()
    _require_owned_schema(db, schema_id, owner_id)

    draft = _ensure_draft(db, schema_id)
    now = _now()
    updates = {"definition": body.definition.model_dump()}
    db.schema_versions.update_one({"id": draft["id"]}, {"$set": updates})

    schema_set = {"updated_at": now, "status": "draft"}
    if body.schema_title:
        schema_set["title"] = body.schema_title.strip()
    db.schemas.update_one({"id": schema_id}, {"$set": schema_set})

    ver = db.schema_versions.find_one({"id": draft["id"]}, {"_id": 0})
    return _version_out(ver)
