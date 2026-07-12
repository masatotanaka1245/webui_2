from fastapi import Depends, FastAPI, File, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .chats import ChatService
from .dependencies import get_current_development_user
from .documents import DocumentError, DocumentService, development_upload_dir
from .open_webui import create_open_webui_client
from .repositories import get_project, list_projects
from .schemas import (
    ApiErrorResponse,
    ChatMessageCreateRequest,
    ChatThread,
    ChatThreadCreateRequest,
    ChatThreadListResponse,
    DevelopmentUser,
    HealthResponse,
    ProjectDetail,
    ProjectDocument,
    ProjectDocumentListResponse,
    ProjectListResponse,
    ProjectSummary,
    RecentDocument,
)

app = FastAPI(title="Open WebUI Business Portal API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.state.open_webui_client = create_open_webui_client()
app.state.document_service = DocumentService(development_upload_dir(), app.state.open_webui_client)
app.state.chat_service = ChatService(app.state.document_service, app.state.open_webui_client)


def api_error(status_code: int, code: str, message: str, details: object | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


@app.exception_handler(DocumentError)
async def document_error_handler(_: Request, error: DocumentError) -> JSONResponse:
    return api_error(error.status_code, error.code, error.message, error.details)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
    if any("file" in item.get("loc", []) for item in error.errors()):
        return api_error(400, "FILE_REQUIRED", "アップロードする資料を選択してください。")
    return api_error(400, "VALIDATION_ERROR", "入力内容を確認してください。")


def document_service() -> DocumentService:
    return app.state.document_service


def chat_service() -> ChatService:
    return app.state.chat_service


def project_or_error(project_id: str) -> ProjectDetail:
    project = get_project(project_id)
    if project is None:
        raise DocumentError(404, "PROJECT_NOT_FOUND", "指定された案件が見つかりません。")
    return project


def project_view(project: ProjectDetail) -> ProjectDetail:
    documents = document_service().list_documents(project.id)
    recent_documents = [
        RecentDocument(id=document.id, name=document.filename, updated_at=document.updated_at)
        for document in sorted(documents, key=lambda item: item.updated_at, reverse=True)[:3]
    ]
    return project.model_copy(
        update={
            "document_count": len(documents),
            "recent_documents": recent_documents,
            "openwebui_knowledge_id": document_service().knowledge_id_for_project(project.id),
            "rag_synced_document_count": sum(
                document.rag_sync_status == "synced" for document in documents
            ),
            "chat_thread_count": len(chat_service().list_threads(project.id)),
            "recent_chats": [
                {"id": thread.id, "title": thread.title, "updated_at": thread.updated_at}
                for thread in chat_service().list_threads(project.id)[:3]
            ],
        }
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        open_webui_client="mock" if app.state.open_webui_client.__class__.__name__.startswith("Mock") else "live",
    )


@app.get("/api/v1/projects", response_model=ProjectListResponse)
def projects(_: DevelopmentUser = Depends(get_current_development_user)) -> ProjectListResponse:
    return ProjectListResponse(
        items=[ProjectSummary(**project_view(project).model_dump()) for project in list_projects()]
    )


@app.get("/api/v1/projects/{project_id}", response_model=ProjectDetail)
def project_detail(
    project_id: str,
    _: DevelopmentUser = Depends(get_current_development_user),
) -> ProjectDetail:
    return project_view(project_or_error(project_id))


@app.get(
    "/api/v1/projects/{project_id}/documents",
    response_model=ProjectDocumentListResponse,
    responses={404: {"model": ApiErrorResponse}},
)
def documents(
    project_id: str,
    _: DevelopmentUser = Depends(get_current_development_user),
) -> ProjectDocumentListResponse:
    project_or_error(project_id)
    return ProjectDocumentListResponse(items=document_service().list_documents(project_id))


@app.post(
    "/api/v1/projects/{project_id}/documents",
    response_model=ProjectDocument,
    responses={400: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}, 500: {"model": ApiErrorResponse}},
)
async def upload_document(
    project_id: str,
    file: UploadFile | None = File(default=None),
    user: DevelopmentUser = Depends(get_current_development_user),
) -> ProjectDocument:
    project_or_error(project_id)
    return await document_service().upload_document(project_id, file, user)


@app.get(
    "/api/v1/projects/{project_id}/documents/{document_id}",
    response_model=ProjectDocument,
    responses={404: {"model": ApiErrorResponse}},
)
def document_detail(
    project_id: str,
    document_id: str,
    _: DevelopmentUser = Depends(get_current_development_user),
) -> ProjectDocument:
    project_or_error(project_id)
    document = document_service().get_document(project_id, document_id)
    if document is None:
        raise DocumentError(404, "DOCUMENT_NOT_FOUND", "指定された資料が見つかりません。")
    return document


@app.post(
    "/api/v1/projects/{project_id}/documents/{document_id}/sync",
    response_model=ProjectDocument,
    responses={404: {"model": ApiErrorResponse}, 409: {"model": ApiErrorResponse}, 502: {"model": ApiErrorResponse}},
)
async def sync_document(
    project_id: str,
    document_id: str,
    _: DevelopmentUser = Depends(get_current_development_user),
) -> ProjectDocument:
    project = project_or_error(project_id)
    return await document_service().sync_document(project_id, document_id, project.name)


@app.get(
    "/api/v1/projects/{project_id}/documents/{document_id}/sync-status",
    response_model=ProjectDocument,
    responses={404: {"model": ApiErrorResponse}},
)
def sync_status(
    project_id: str,
    document_id: str,
    _: DevelopmentUser = Depends(get_current_development_user),
) -> ProjectDocument:
    project_or_error(project_id)
    document = document_service().get_document(project_id, document_id)
    if document is None:
        raise DocumentError(404, "DOCUMENT_NOT_FOUND", "指定された資料が見つかりません。")
    return document


@app.get(
    "/api/v1/projects/{project_id}/chat-threads",
    response_model=ChatThreadListResponse,
    responses={404: {"model": ApiErrorResponse}},
)
def chat_threads(
    project_id: str,
    _: DevelopmentUser = Depends(get_current_development_user),
) -> ChatThreadListResponse:
    project_or_error(project_id)
    return ChatThreadListResponse(items=chat_service().list_threads(project_id))


@app.post(
    "/api/v1/projects/{project_id}/chat-threads",
    response_model=ChatThread,
    responses={400: {"model": ApiErrorResponse}, 404: {"model": ApiErrorResponse}},
)
def create_chat_thread(
    project_id: str,
    payload: ChatThreadCreateRequest,
    user: DevelopmentUser = Depends(get_current_development_user),
) -> ChatThread:
    project_or_error(project_id)
    return chat_service().create_thread(project_id, payload.title, user)


@app.get(
    "/api/v1/projects/{project_id}/chat-threads/{thread_id}",
    response_model=ChatThread,
    responses={404: {"model": ApiErrorResponse}},
)
def chat_thread_detail(
    project_id: str,
    thread_id: str,
    _: DevelopmentUser = Depends(get_current_development_user),
) -> ChatThread:
    project_or_error(project_id)
    thread = chat_service().get_thread(project_id, thread_id)
    if thread is None:
        raise DocumentError(404, "CHAT_THREAD_NOT_FOUND", "指定されたチャットスレッドが見つかりません。")
    return thread


@app.post(
    "/api/v1/projects/{project_id}/chat-threads/{thread_id}/messages",
    response_model=ChatThread,
    responses={404: {"model": ApiErrorResponse}, 409: {"model": ApiErrorResponse}, 502: {"model": ApiErrorResponse}},
)
async def create_chat_message(
    project_id: str,
    thread_id: str,
    payload: ChatMessageCreateRequest,
    _: DevelopmentUser = Depends(get_current_development_user),
) -> ChatThread:
    project_or_error(project_id)
    return await chat_service().add_message(project_id, thread_id, payload.content, payload.model_id)
