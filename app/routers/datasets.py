from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import require_role
from app.deps import get_current_user, get_store
from app.models import (
    AccessRequestCreate,
    AccessRequestRecord,
    DatasetCreate,
    DatasetRecord,
    DatasetUpdate,
    Role,
)
from app.storage import Storage

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetRecord, status_code=status.HTTP_201_CREATED)
def create_dataset(
    payload: DatasetCreate,
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> DatasetRecord:
    require_role(user, {Role.admin, Role.researcher})
    return store.create_dataset(payload, owner_id=user.id)


@router.get("", response_model=list[DatasetRecord])
def list_datasets(
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> list[DatasetRecord]:
    return store.list_datasets()


@router.get("/{dataset_id}", response_model=DatasetRecord)
def get_dataset(
    dataset_id: str,
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> DatasetRecord:
    dataset = store.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.patch("/{dataset_id}", response_model=DatasetRecord)
def update_dataset(
    dataset_id: str,
    payload: DatasetUpdate,
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> DatasetRecord:
    dataset = store.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    if dataset.locked and user.role != Role.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dataset is locked")
    if user.role != Role.admin and dataset.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to edit dataset")
    updated = store.update_dataset(dataset_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return updated


@router.post("/{dataset_id}/lock", response_model=DatasetRecord)
def lock_dataset(
    dataset_id: str,
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> DatasetRecord:
    require_role(user, {Role.admin})
    dataset = store.set_dataset_lock(dataset_id, True)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.post("/{dataset_id}/unlock", response_model=DatasetRecord)
def unlock_dataset(
    dataset_id: str,
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> DatasetRecord:
    require_role(user, {Role.admin})
    dataset = store.set_dataset_lock(dataset_id, False)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.post("/{dataset_id}/requests", response_model=AccessRequestRecord, status_code=201)
def request_access(
    dataset_id: str,
    payload: AccessRequestCreate,
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> AccessRequestRecord:
    dataset = store.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return store.create_access_request(dataset_id, user.id, payload)


@router.get("/{dataset_id}/requests", response_model=list[AccessRequestRecord])
def list_requests(
    dataset_id: str,
    store: Storage = Depends(get_store),
    user=Depends(get_current_user),
) -> list[AccessRequestRecord]:
    dataset = store.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    if user.role != Role.admin and dataset.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view requests")
    return store.list_access_requests(dataset_id)
