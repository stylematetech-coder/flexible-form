from pymongo import MongoClient, ASCENDING
from .config import MONGO_URI, MONGO_DB

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client


def get_db():
    return get_client()[MONGO_DB]


def ensure_indexes():
    db = get_db()
    db.schemas.create_index([("slug", ASCENDING)], unique=True)
    db.schemas.create_index([("owner_id", ASCENDING)])
    db.schema_versions.create_index([("schema_id", ASCENDING), ("version", ASCENDING)], unique=True)
    db.schema_versions.create_index([("preview_token", ASCENDING)], sparse=True)
    db.responses.create_index([("schema_id", ASCENDING)])
