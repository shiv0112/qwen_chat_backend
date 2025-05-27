# app/core/redis_store.py

import json
import uuid
import os
import redis
from typing import List

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SESSION_TTL = int(os.getenv("SESSION_TTL", 3600))         # in seconds
MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", 100))        # max concurrent sessions
SESSION_INDEX_KEY = "session_index"                       # Redis sorted set key

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def generate_session_id() -> str:
    return str(uuid.uuid4())

def get_session_key(session_id: str) -> str:
    return f"session:{session_id}"

def track_session(session_id: str):
    # Add session with current timestamp (for eviction policy)
    r.zadd(SESSION_INDEX_KEY, {session_id: r.time()[0]})
    # If over limit, evict oldest session
    total_sessions = r.zcard(SESSION_INDEX_KEY)
    if total_sessions > MAX_SESSIONS:
        oldest = r.zrange(SESSION_INDEX_KEY, 0, 0)
        if oldest:
            oldest_id = oldest[0]
            r.delete(get_session_key(oldest_id))     # Delete chat history
            r.zrem(SESSION_INDEX_KEY, oldest_id)     # Remove from index

def create_session_if_missing(session_id: str):
    key = get_session_key(session_id)
    if not r.exists(key):
        r.set(key, json.dumps([]))
    r.expire(key, SESSION_TTL)
    track_session(session_id)

def get_chat_history(session_id: str) -> List[dict]:
    key = get_session_key(session_id)
    raw = r.get(key)
    return json.loads(raw) if raw else []

def save_message(session_id: str, role: str, content: str):
    key = get_session_key(session_id)
    history = get_chat_history(session_id)
    history.append({"role": role, "content": content})
    r.set(key, json.dumps(history))
    r.expire(key, SESSION_TTL)
