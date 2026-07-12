from datetime import datetime, timezone

from .schemas import ProjectDetail, ProjectSummary, RecentChat, RecentDocument


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


_PROJECTS = [
    ProjectDetail(
        id="project-central-library",
        name="中央図書館改修計画",
        code="LIB-2026-001",
        status="active",
        overview="改修計画に関する設計資料、調査結果、関係者との検討を案件単位で管理します。",
        location="東京都千代田区",
        period="2026-04-01 〜 2027-03-31",
        document_count=3,
        chat_thread_count=2,
        updated_at=_timestamp("2026-07-12T09:30:00"),
        recent_documents=[
            RecentDocument(
                id="doc-library-survey",
                name="現地調査メモ.pdf",
                updated_at=_timestamp("2026-07-12T09:30:00"),
            ),
            RecentDocument(
                id="doc-library-requirements",
                name="要求整理.md",
                updated_at=_timestamp("2026-07-10T13:00:00"),
            ),
        ],
        recent_chats=[
            RecentChat(
                id="chat-library-issues",
                title="調査結果の要点整理",
                updated_at=_timestamp("2026-07-12T10:00:00"),
            ),
            RecentChat(
                id="chat-library-schedule",
                title="改修工程の確認",
                updated_at=_timestamp("2026-07-11T16:20:00"),
            ),
        ],
    ),
    ProjectDetail(
        id="project-river-monitoring",
        name="河川モニタリング調査",
        code="RIV-2026-014",
        status="planning",
        overview="河川環境の測定計画と観測資料を整理し、調査準備を進める案件です。",
        location="埼玉県川越市",
        period="2026-08-01 〜 2026-12-20",
        document_count=1,
        chat_thread_count=1,
        updated_at=_timestamp("2026-07-11T15:45:00"),
        recent_documents=[
            RecentDocument(
                id="doc-river-plan",
                name="観測計画（案）.pdf",
                updated_at=_timestamp("2026-07-11T15:45:00"),
            )
        ],
        recent_chats=[
            RecentChat(
                id="chat-river-preparation",
                title="観測項目の検討",
                updated_at=_timestamp("2026-07-09T11:15:00"),
            )
        ],
    ),
]


def list_projects() -> list[ProjectSummary]:
    return [ProjectSummary(**project.model_dump()) for project in _PROJECTS]


def get_project(project_id: str) -> ProjectDetail | None:
    return next((project for project in _PROJECTS if project.id == project_id), None)
