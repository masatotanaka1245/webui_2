from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ProjectStatus = Literal["planning", "active", "completed", "on_hold"]
DocumentStatus = Literal["uploaded", "processing", "ready", "failed"]
RagSyncStatus = Literal["not_started", "pending", "processing", "synced", "failed"]
ChatRole = Literal["user", "assistant"]


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
    rag_synced_document_count: int = Field(default=0, ge=0)


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


class ChatCitation(BaseModel):
    source_type: str
    source_name: str
    reference: str | None = None


class ChatMessage(BaseModel):
    id: str
    thread_id: str
    role: ChatRole
    content: str
    citations: list[ChatCitation] = Field(default_factory=list)
    model_id: str | None = None
    created_at: datetime
    error_message: str | None = None


class ChatThread(BaseModel):
    id: str
    project_id: str
    title: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessage] = Field(default_factory=list)


class ChatThreadListResponse(BaseModel):
    items: list[ChatThread]


class ChatThreadCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=12000)
    model_id: str = Field(default="gemma4:e2b", min_length=1, max_length=120)


class ApiErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ApiErrorResponse(BaseModel):
    error: ApiErrorBody
