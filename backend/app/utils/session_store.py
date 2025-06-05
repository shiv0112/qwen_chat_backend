# app/session.py

import time
from typing import Dict
from app.config import DEFAULT_TTL

# In-memory session storage
SESSION_STORE: Dict[str, Dict] = {}

def _is_expired(session_data: Dict) -> bool:
    return time.time() > session_data["expiry"]

def _cleanup_expired_sessions():
    expired_keys = [key for key, value in SESSION_STORE.items() if _is_expired(value)]
    for key in expired_keys:
        del SESSION_STORE[key]

def get_session(session_id: str) -> Dict:
    _cleanup_expired_sessions()
    session = SESSION_STORE.get(session_id)
    if session and not _is_expired(session):
        return session
    return {
        "messages": [],
        "tokens_used": 0
    }

def save_session(session_id: str, session_data: Dict, ttl: int = DEFAULT_TTL):
    _cleanup_expired_sessions()
    SESSION_STORE[session_id] = {
        **session_data,
        "expiry": time.time() + ttl
    }

def delete_session(session_id: str):
    SESSION_STORE.pop(session_id, None)

def clear_all_sessions():
    SESSION_STORE.clear()

def get_all_sessions():
    _cleanup_expired_sessions()
    return {
        session_id: {
            "expires_in": f"{int((session_data['expiry'] - time.time()) // 60)} minutes and "
                          f"{int((session_data['expiry'] - time.time()) % 60)} seconds",
            "tokens_used": session_data.get("tokens_used", 0),
        }
        for session_id, session_data in SESSION_STORE.items()
    }
