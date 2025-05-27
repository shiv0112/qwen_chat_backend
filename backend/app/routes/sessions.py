from fastapi import APIRouter
from app.utils.session_store import (
    get_all_sessions,
    delete_session,
    clear_all_sessions,
)

router = APIRouter()

@router.get("/")
def list_sessions():
    """
    List all active sessions with metadata.
    """
    return get_all_sessions()

@router.delete("/{session_id}")
def delete_specific_session(session_id: str):
    """
    Delete a specific session by ID.
    """
    delete_session(session_id)
    return {"message": f"Session '{session_id}' deleted."}

@router.delete("/")
def delete_all_sessions():
    """
    Clear all sessions from memory.
    """
    clear_all_sessions()
    return {"message": "All sessions deleted."}
