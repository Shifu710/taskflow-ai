from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.entities import WorkspaceMember

PERMISSIONS = {
    "view_workflows": {"owner", "admin", "operator", "viewer", "guest"},
    "create_workflow": {"owner", "admin", "operator"},
    "edit_workflow": {"owner", "admin", "operator"},
    "run_workflow": {"owner", "admin", "operator", "viewer", "guest"},
    "approve_demo_action": {"owner", "admin", "operator", "guest"},
    "manage_tools": {"owner", "admin"},
    "view_usage": {"owner", "admin", "operator", "viewer", "guest"},
    "manage_settings": {"owner", "admin"},
}


def role_for(db: Session, workspace_id: str, user_id: str) -> str:
    member = db.query(WorkspaceMember).filter_by(workspace_id=workspace_id, user_id=user_id).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a workspace member")
    return member.role


def require_permission(db: Session, workspace_id: str, user_id: str, permission: str) -> str:
    role = role_for(db, workspace_id, user_id)
    if role not in PERMISSIONS[permission]:
        raise HTTPException(status_code=403, detail=f"Role {role} cannot {permission}")
    return role
