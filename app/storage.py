from __future__ import annotations

from datetime import datetime
from typing import Protocol
from uuid import uuid4

from app.models import (
    AccessRequestCreate,
    AccessRequestRecord,
    DatasetCreate,
    DatasetRecord,
    DatasetUpdate,
    UserCreate,
    UserRecord,
)
from app.auth import hash_password


class Storage(Protocol):
    def create_user(self, user: UserCreate) -> UserRecord:
        ...

    def get_user_by_email(self, email: str) -> UserRecord | None:
        ...

    def get_user(self, user_id: str) -> UserRecord | None:
        ...

    def list_users(self) -> list[UserRecord]:
        ...

    def create_dataset(self, data: DatasetCreate, owner_id: str) -> DatasetRecord:
        ...

    def list_datasets(self) -> list[DatasetRecord]:
        ...

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        ...

    def update_dataset(self, dataset_id: str, data: DatasetUpdate) -> DatasetRecord | None:
        ...

    def set_dataset_lock(self, dataset_id: str, locked: bool) -> DatasetRecord | None:
        ...

    def create_access_request(
        self, dataset_id: str, requester_id: str, payload: AccessRequestCreate
    ) -> AccessRequestRecord:
        ...

    def list_access_requests(self, dataset_id: str) -> list[AccessRequestRecord]:
        ...


class InMemoryStore:
    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}
        self._datasets: dict[str, DatasetRecord] = {}
        self._requests: dict[str, AccessRequestRecord] = {}

    def create_user(self, user: UserCreate) -> UserRecord:
        user_id = str(uuid4())
        record = UserRecord(
            id=user_id,
            email=user.email,
            role=user.role,
            hashed_password=hash_password(user.password),
        )
        self._users[user_id] = record
        return record

    def get_user_by_email(self, email: str) -> UserRecord | None:
        return next((user for user in self._users.values() if user.email == email), None)

    def get_user(self, user_id: str) -> UserRecord | None:
        return self._users.get(user_id)

    def list_users(self) -> list[UserRecord]:
        return list(self._users.values())

    def create_dataset(self, data: DatasetCreate, owner_id: str) -> DatasetRecord:
        dataset_id = str(uuid4())
        record = DatasetRecord(
            id=dataset_id,
            drug_name=data.drug_name,
            study_id=data.study_id,
            dataset_type=data.dataset_type,
            metadata=data.metadata,
            file_name=data.file_name,
            owner_id=owner_id,
        )
        self._datasets[dataset_id] = record
        return record

    def list_datasets(self) -> list[DatasetRecord]:
        return list(self._datasets.values())

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        return self._datasets.get(dataset_id)

    def update_dataset(self, dataset_id: str, data: DatasetUpdate) -> DatasetRecord | None:
        record = self._datasets.get(dataset_id)
        if not record:
            return None
        updated = record.model_copy(update=data.model_dump(exclude_unset=True))
        updated.updated_at = datetime.utcnow()
        self._datasets[dataset_id] = updated
        return updated

    def set_dataset_lock(self, dataset_id: str, locked: bool) -> DatasetRecord | None:
        record = self._datasets.get(dataset_id)
        if not record:
            return None
        updated = record.model_copy(update={"locked": locked, "updated_at": datetime.utcnow()})
        self._datasets[dataset_id] = updated
        return updated

    def create_access_request(
        self, dataset_id: str, requester_id: str, payload: AccessRequestCreate
    ) -> AccessRequestRecord:
        request_id = str(uuid4())
        record = AccessRequestRecord(
            id=request_id,
            dataset_id=dataset_id,
            requester_id=requester_id,
            reason=payload.reason,
        )
        self._requests[request_id] = record
        return record

    def list_access_requests(self, dataset_id: str) -> list[AccessRequestRecord]:
        return [req for req in self._requests.values() if req.dataset_id == dataset_id]


class MongoStore:
    def __init__(self, uri: str, database: str) -> None:
        from pymongo import MongoClient

        self._client = MongoClient(uri)
        self._db = self._client[database]
        self._users = self._db["users"]
        self._datasets = self._db["datasets"]
        self._requests = self._db["access_requests"]
        self._users.create_index("email", unique=True)
        self._datasets.create_index("owner_id")
        self._requests.create_index("dataset_id")

    def create_user(self, user: UserCreate) -> UserRecord:
        user_id = str(uuid4())
        record = UserRecord(
            id=user_id,
            email=user.email,
            role=user.role,
            hashed_password=hash_password(user.password),
        )
        self._users.insert_one(record.model_dump())
        return record

    def get_user_by_email(self, email: str) -> UserRecord | None:
        doc = self._users.find_one({"email": email})
        return UserRecord(**doc) if doc else None

    def get_user(self, user_id: str) -> UserRecord | None:
        doc = self._users.find_one({"id": user_id})
        return UserRecord(**doc) if doc else None

    def list_users(self) -> list[UserRecord]:
        return [UserRecord(**doc) for doc in self._users.find({})]

    def create_dataset(self, data: DatasetCreate, owner_id: str) -> DatasetRecord:
        dataset_id = str(uuid4())
        record = DatasetRecord(
            id=dataset_id,
            drug_name=data.drug_name,
            study_id=data.study_id,
            dataset_type=data.dataset_type,
            metadata=data.metadata,
            file_name=data.file_name,
            owner_id=owner_id,
        )
        self._datasets.insert_one(record.model_dump())
        return record

    def list_datasets(self) -> list[DatasetRecord]:
        return [DatasetRecord(**doc) for doc in self._datasets.find({})]

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        doc = self._datasets.find_one({"id": dataset_id})
        return DatasetRecord(**doc) if doc else None

    def update_dataset(self, dataset_id: str, data: DatasetUpdate) -> DatasetRecord | None:
        update = data.model_dump(exclude_unset=True)
        if update:
            update["updated_at"] = datetime.utcnow()
            self._datasets.update_one({"id": dataset_id}, {"$set": update})
        return self.get_dataset(dataset_id)

    def set_dataset_lock(self, dataset_id: str, locked: bool) -> DatasetRecord | None:
        self._datasets.update_one(
            {"id": dataset_id}, {"$set": {"locked": locked, "updated_at": datetime.utcnow()}}
        )
        return self.get_dataset(dataset_id)

    def create_access_request(
        self, dataset_id: str, requester_id: str, payload: AccessRequestCreate
    ) -> AccessRequestRecord:
        request_id = str(uuid4())
        record = AccessRequestRecord(
            id=request_id,
            dataset_id=dataset_id,
            requester_id=requester_id,
            reason=payload.reason,
        )
        self._requests.insert_one(record.model_dump())
        return record

    def list_access_requests(self, dataset_id: str) -> list[AccessRequestRecord]:
        return [AccessRequestRecord(**doc) for doc in self._requests.find({"dataset_id": dataset_id})]
