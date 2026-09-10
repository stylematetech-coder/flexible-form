from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class Option(BaseModel):
    value: str
    label: str


class ShowIf(BaseModel):
    field: str
    op: Literal["eq", "neq", "includes", "notIncludes"]
    value: Any


class Step(BaseModel):
    id: str
    type: Literal["single", "multi", "text", "textarea", "number", "info"]
    title: str
    required: bool = False
    options: list[Option] = Field(default_factory=list)
    showIf: Optional[ShowIf] = None


class FormSettings(BaseModel):
    require_identity: list[str] = Field(default_factory=lambda: ["name", "phone"])
    one_response_per: Optional[str] = None


class FormDefinition(BaseModel):
    version: str = "1.0"
    locale: str = "zh-TW"
    settings: FormSettings = Field(default_factory=FormSettings)
    steps: list[Step] = Field(default_factory=list)


class SchemaCreate(BaseModel):
    title: str
    slug: str


class SchemaOut(BaseModel):
    id: str
    slug: str
    title: str
    status: str
    active_version: Optional[int] = None
    owner_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VersionCreate(BaseModel):
    definition: Optional[FormDefinition] = None


class VersionPatch(BaseModel):
    definition: FormDefinition


class VersionOut(BaseModel):
    id: str
    schema_id: str
    version: int
    status: Literal["draft", "preview", "published"]
    definition: FormDefinition
    created_at: datetime
    published_at: Optional[datetime] = None
    preview_token: Optional[str] = None


class Identity(BaseModel):
    name: str = ""
    phone: str = ""


class ResponseCreate(BaseModel):
    identity: Identity = Field(default_factory=Identity)
    answers: dict[str, Any] = Field(default_factory=dict)


class ResponsePatch(BaseModel):
    identity: Optional[Identity] = None
    answers: Optional[dict[str, Any]] = None


class ResponseOut(BaseModel):
    id: str
    schema_id: str
    version: int
    status: Literal["in_progress", "submitted"]
    identity: Identity
    answers: dict[str, Any]
    created_at: datetime
    submitted_at: Optional[datetime] = None


class PublicFormOut(BaseModel):
    schema_id: str
    slug: str
    title: str
    version: int
    definition: FormDefinition
    mode: Literal["public", "preview"] = "public"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class AiChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)


class AiChatResponse(BaseModel):
    reply: str
    proposed_definition: Optional[dict[str, Any]] = None
    proposed_schema_title: Optional[str] = None


class AiApplyRequest(BaseModel):
    definition: FormDefinition
    schema_title: Optional[str] = None
