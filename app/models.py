from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, EmailStr


class Role(str, Enum):
    admin = "admin"
    researcher = "researcher"
    viewer = "viewer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Role = Role.viewer


class UserPublic(BaseModel):
    id: str
    email: EmailStr
    role: Role


class UserRecord(UserPublic):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DatasetCreate(BaseModel):
    drug_name: str
    study_id: str
    dataset_type: str
    metadata: dict = Field(default_factory=dict)
    file_name: str | None = None


class DatasetUpdate(BaseModel):
    drug_name: str | None = None
    study_id: str | None = None
    dataset_type: str | None = None
    metadata: dict | None = None
    file_name: str | None = None


class DatasetRecord(BaseModel):
    id: str
    drug_name: str
    study_id: str
    dataset_type: str
    metadata: dict
    file_name: str | None
    owner_id: str
    locked: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AccessRequestCreate(BaseModel):
    reason: str


class AccessRequestRecord(BaseModel):
    id: str
    dataset_id: str
    requester_id: str
    reason: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RoleUpgradeRequestCreate(BaseModel):
    requested_role: Role
    reason: str


class RoleUpgradeRequestRecord(BaseModel):
    id: str
    requester_id: str
    requested_role: Role
    reason: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLogRecord(BaseModel):
    id: str
    dataset_id: str
    actor_id: str
    action: str
    details: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
