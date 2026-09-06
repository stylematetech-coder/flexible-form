from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from ulid import ULID

from ..db import get_db
from ..models import (
    PublicFormOut,
    FormDefinition,
    ResponseCreate,
    ResponsePatch,
    ResponseOut,
    Identity,
)

router = APIRouter(prefix="/public", tags=["public"])


def _now():
    return datetime.now(timezone.utc)


def _response_out(doc) -> ResponseOut:
    return ResponseOut(
        id=doc["id"],
        schema_id=doc["schema_id"],
        version=doc["version"],
        status=doc["status"],
        identity=Identity.model_validate(doc.get("identity") or {}),
        answers=doc.get("answers") or {},
        created_at=doc["created_at"],
        submitted_at=doc.get("submitted_at"),
    )


@router.get("/forms/{slug}", response_model=PublicFormOut)
def get_public_form(slug: str):
    db = get_db()
    schema = db.schemas.find_one({"slug": slug}, {"_id": 0})
    if not schema:
        raise HTTPException(404, "form not found")
    if schema.get("active_version") is None:
        raise HTTPException(404, "form not published")
    ver = db.schema_versions.find_one(
        {
            "schema_id": schema["id"],
            "version": schema["active_version"],
            "status": "published",
        },
        {"_id": 0},
    )
    if not ver:
        raise HTTPException(404, "published version not found")
    return PublicFormOut(
        schema_id=schema["id"],
        slug=schema["slug"],
        title=schema["title"],
        version=ver["version"],
        definition=FormDefinition.model_validate(ver["definition"]),
        mode="public",
    )


@router.get("/preview/{token}", response_model=PublicFormOut)
def get_preview_form(token: str):
    db = get_db()
    ver = db.schema_versions.find_one({"preview_token": token}, {"_id": 0})
    if not ver:
        raise HTTPException(404, "preview not found")
    schema = db.schemas.find_one({"id": ver["schema_id"]}, {"_id": 0})
    if not schema:
        raise HTTPException(404, "schema not found")
    return PublicFormOut(
        schema_id=schema["id"],
        slug=schema["slug"],
        title=schema["title"],
        version=ver["version"],
        definition=FormDefinition.model_validate(ver["definition"]),
        mode="preview",
    )


@router.post("/forms/{slug}/responses", response_model=ResponseOut)
def create_response(slug: str, body: ResponseCreate):
    db = get_db()
    schema = db.schemas.find_one({"slug": slug})
    if not schema or schema.get("active_version") is None:
        raise HTTPException(404, "form not found or not published")
    now = _now()
    doc = {
        "id": str(ULID()),
        "schema_id": schema["id"],
        "version": schema["active_version"],
        "status": "in_progress",
        "identity": body.identity.model_dump(),
        "answers": body.answers,
        "created_at": now,
        "submitted_at": None,
    }
    db.responses.insert_one(doc)
    return _response_out(doc)


@router.patch("/responses/{rid}", response_model=ResponseOut)
def patch_response(rid: str, body: ResponsePatch):
    db = get_db()
    doc = db.responses.find_one({"id": rid})
    if not doc:
        raise HTTPException(404, "response not found")
    if doc["status"] == "submitted":
        raise HTTPException(400, "already submitted")
    updates = {}
    if body.identity is not None:
        updates["identity"] = body.identity.model_dump()
    if body.answers is not None:
        updates["answers"] = body.answers
    if updates:
        db.responses.update_one({"id": rid}, {"$set": updates})
    doc = db.responses.find_one({"id": rid}, {"_id": 0})
    return _response_out(doc)


@router.post("/responses/{rid}/submit", response_model=ResponseOut)
def submit_response(rid: str):
    db = get_db()
    doc = db.responses.find_one({"id": rid})
    if not doc:
        raise HTTPException(404, "response not found")
    if doc["status"] == "submitted":
        raise HTTPException(400, "already submitted")

    # Load definition for validation
    ver = db.schema_versions.find_one(
        {"schema_id": doc["schema_id"], "version": doc["version"]}
    )
    if not ver:
        raise HTTPException(400, "version missing")
    definition = FormDefinition.model_validate(ver["definition"])
    identity = doc.get("identity") or {}
    for field in definition.settings.require_identity:
        if not (identity.get(field) or "").strip():
            raise HTTPException(400, f"identity.{field} required")

    answers = doc.get("answers") or {}
    for step in definition.steps:
        if step.type == "info":
            continue
        if not _step_visible(step, answers):
            continue
        if step.required:
            val = answers.get(step.id)
            if val is None or val == "" or val == []:
                raise HTTPException(400, f"step {step.id} required")

    now = _now()
    db.responses.update_one(
        {"id": rid},
        {"$set": {"status": "submitted", "submitted_at": now}},
    )
    doc = db.responses.find_one({"id": rid}, {"_id": 0})
    return _response_out(doc)


def _step_visible(step, answers: dict) -> bool:
    if not step.showIf:
        return True
    sf = step.showIf
    raw = answers.get(sf.field)
    if sf.op == "eq":
        return raw == sf.value
    if sf.op == "neq":
        return raw != sf.value
    if sf.op == "includes":
        if isinstance(raw, list):
            return sf.value in raw
        return False
    if sf.op == "notIncludes":
        if isinstance(raw, list):
            return sf.value not in raw
        return True
    return True
