"""Seed a sample schema with slug `demo`."""
from datetime import datetime, timezone
from ulid import ULID

from .db import get_db, ensure_indexes


def seed_demo(force: bool = False):
    db = get_db()
    ensure_indexes()
    existing = db.schemas.find_one({"slug": "demo"})
    if existing and not force:
        print(f"demo schema already exists: {existing['id']}")
        return existing["id"]

    if existing and force:
        sid = existing["id"]
        db.schema_versions.delete_many({"schema_id": sid})
        db.responses.delete_many({"schema_id": sid})
        db.schemas.delete_one({"id": sid})

    now = datetime.now(timezone.utc)
    schema_id = str(ULID())
    version_id = str(ULID())
    preview_token = str(ULID())

    definition = {
        "version": "1.0",
        "locale": "zh-TW",
        "settings": {
            "require_identity": ["name", "phone"],
            "one_response_per": None,
        },
        "steps": [
            {
                "id": "q_role",
                "type": "single",
                "title": "您的身份是？",
                "required": True,
                "options": [
                    {"value": "student", "label": "學生"},
                    {"value": "teacher", "label": "教師"},
                    {"value": "other", "label": "其他"},
                ],
                "showIf": None,
            },
            {
                "id": "q_school",
                "type": "text",
                "title": "就讀學校名稱",
                "required": True,
                "options": [],
                "showIf": {"field": "q_role", "op": "eq", "value": "student"},
            },
            {
                "id": "q_topics",
                "type": "multi",
                "title": "感興趣的主題（可複選）",
                "required": True,
                "options": [
                    {"value": "ai", "label": "人工智慧"},
                    {"value": "web", "label": "網頁開發"},
                    {"value": "data", "label": "資料科學"},
                ],
                "showIf": None,
            },
            {
                "id": "q_score",
                "type": "number",
                "title": "自我評分（1-10）",
                "required": False,
                "options": [],
                "showIf": None,
            },
            {
                "id": "q_feedback",
                "type": "textarea",
                "title": "其他建議",
                "required": False,
                "options": [],
                "showIf": None,
            },
            {
                "id": "info_thanks",
                "type": "info",
                "title": "感謝您抽空填寫此問卷！",
                "required": False,
                "options": [],
                "showIf": None,
            },
        ],
    }

    db.schemas.insert_one(
        {
            "id": schema_id,
            "slug": "demo",
            "title": "示範問卷",
            "status": "published",
            "active_version": 1,
            "created_at": now,
            "updated_at": now,
        }
    )
    db.schema_versions.insert_one(
        {
            "id": version_id,
            "schema_id": schema_id,
            "version": 1,
            "status": "published",
            "definition": definition,
            "created_at": now,
            "published_at": now,
            "preview_token": preview_token,
        }
    )
    # Also create a draft v2 for designer editing
    draft_id = str(ULID())
    db.schema_versions.insert_one(
        {
            "id": draft_id,
            "schema_id": schema_id,
            "version": 2,
            "status": "draft",
            "definition": definition,
            "created_at": now,
            "published_at": None,
            "preview_token": None,
        }
    )
    print(f"Seeded demo schema={schema_id} version={version_id} preview={preview_token}")
    return schema_id


if __name__ == "__main__":
    seed_demo(force=True)
