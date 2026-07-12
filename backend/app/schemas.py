from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ProjectStatus = Literal["planning", "active", "completed", "on_hold"]


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


class ProjectListResponse(BaseModel):
    items: list[ProjectSummary]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    open_webui_client: Literal["mock"]
