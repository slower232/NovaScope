"""Caché SQLite de respuestas externas con TTL. Permite usar datos almacenados sin internet."""
import hashlib, json
from datetime import datetime, timedelta
from sqlalchemy import select
from database.connection import get_session
from database.models import ApiCache


def make_key(source: str, **params) -> str:
    raw = source + json.dumps(params, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:64]


def get(key: str, ttl_hours: float, allow_stale: bool = False):
    """Devuelve (payload, fetched_at, is_fresh) o None."""
    with get_session() as s:
        row = s.scalar(select(ApiCache).where(ApiCache.key == key))
        if row is None:
            return None
        fresh = datetime.utcnow() - row.fetched_at <= timedelta(hours=ttl_hours)
        if fresh or allow_stale:
            return json.loads(row.payload), row.fetched_at, fresh
        return None


def put(key: str, source: str, payload) -> None:
    with get_session() as s:
        row = s.get(ApiCache, key)
        data = json.dumps(payload)
        if row:
            row.payload, row.fetched_at = data, datetime.utcnow()
        else:
            s.add(ApiCache(key=key, source=source, payload=data))
        s.commit()
