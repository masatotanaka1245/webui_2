from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ProjectStatus = Literal["planning", "active", "completed", "on_hold"]
DocumentStatus = Literal["uploaded", "processing", "ready", "failed"]
RagSyncStatus = Literal["not_started", "pending", "processing", "synced", "failed"]


class DevelopmentUser(BaseModel):
    user_id: str
    role: str


class RecentDocument(BaseModel):
    id: str
    name: str
    updated_at: datetime


class RecentChat(BaseModel):
    id: str
    title: str
    updated_at: datetime


class ProjectSummary(BaseModel):
    id: str
    name: str
    code: str
    status: ProjectStatus
    location: str
    period: str
    document_count: int = Field(ge=0)
    chat_thread_count: int = Field(ge=0)
    updated_at: datetime


class ProjectDetail(ProjectSummary):
    overview: str
    recent_documents: list[RecentDocument]
    recent_chats: list[RecentChat]
    openwebui_knowledge_id: str | None = None


class ProjectListResponse(BaseModel):
    items: list[ProjectSummary]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    open_webui_client: Literal["mock", "live"]


class ProjectDocument(BaseModel):
    id: str
    project_id: str
    filename: str
    stored_filename: str
    content_type: str
    size_bytes: int = Field(ge=1)
    status: DocumentStatus
    rag_sync_status: RagSyncStatus
    openwebui_file_id: str | None = None
    rag_synced_at: datetime | None = None
    rag_sync_error: str | None = None
    uploaded_by: str
    created_at: datetime
    updated_at: datetime
    error_message: str | None = None


class ProjectDocumentListResponse(BaseModel):
    items: list[ProjectDocument]


class ApiErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ApiErrorResponse(BaseModel):
    error: ApiErrorBody
