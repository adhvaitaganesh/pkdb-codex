from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_role
from app.deps import get_current_user, get_store
from app.models import (
    Role,
    RoleUpgradeRequestCreate,
    RoleUpgradeRequestRecord,
)
from app.storage import Storage

router = APIRouter(prefix="/roles", tags=["roles"])


@router.post("/requests", response_model=RoleUpgradeRequestRecord, status_code=status.HTTP_201_CREATED)
def create_role_request(
    payload: RoleUpgradeRequestCreate,
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> RoleUpgradeRequestRecord:
    if user.role != Role.viewer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role upgrade requests are only for viewers",
        )
    if payload.requested_role == Role.admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin role requires manual assignment",
        )
    return store.create_role_upgrade_request(user.id, payload)


@router.get("/requests", response_model=list[RoleUpgradeRequestRecord])
def list_role_requests(
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> list[RoleUpgradeRequestRecord]:
    require_role(user, {Role.admin})
    return store.list_role_upgrade_requests()


@router.post("/requests/{request_id}/approve", response_model=RoleUpgradeRequestRecord)
def approve_role_request(
    request_id: str,
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> RoleUpgradeRequestRecord:
    require_role(user, {Role.admin})
    request = store.set_role_upgrade_request_status(request_id, "approved")
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    store.update_user_role(request.requester_id, request.requested_role)
    return request


@router.post("/requests/{request_id}/reject", response_model=RoleUpgradeRequestRecord)
def reject_role_request(
    request_id: str,
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> RoleUpgradeRequestRecord:
    require_role(user, {Role.admin})
    request = store.set_role_upgrade_request_status(request_id, "rejected")
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return request
