import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from .open_webui import OpenWebUIClient
from .schemas import DevelopmentUser, ProjectDocument

MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv"}


class DocumentError(Exception):
    def __init__(self, status_code: int, code: str, message: str, details: str | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class DocumentService:
    """Development-only document store with a replaceable Open WebUI client."""

    def __init__(self, storage_dir: Path, open_webui_client: OpenWebUIClient):
        self._storage_dir = storage_dir
        self._open_webui_client = open_webui_client
        self._documents: dict[str, list[ProjectDocument]] = {}
        self._knowledge_ids: dict[str, str] = {}

    def list_documents(self, project_id: str) -> list[ProjectDocument]:
        return list(self._documents.get(project_id, []))

    def get_document(self, project_id: str, document_id: str) -> ProjectDocument | None:
        return next(
            (document for document in self._documents.get(project_id, []) if document.id == document_id),
            None,
        )

    def knowledge_id_for_project(self, project_id: str) -> str | None:
        return self._knowledge_ids.get(project_id)

    async def upload_document(
        self,
        project_id: str,
        upload: UploadFile | None,
        user: DevelopmentUser,
    ) -> ProjectDocument:
        if upload is None or not upload.filename:
            raise DocumentError(400, "FILE_REQUIRED", "アップロードする資料を選択してください。")

        filename = upload.filename
        if Path(filename).name != filename or "\\" in filename:
            raise DocumentError(400, "INVALID_FILENAME", "資料ファイル名が不正です。")

        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise DocumentError(400, "UNSUPPORTED_FILE_TYPE", "対応していない資料形式です。")

        content = await upload.read()
        if not content:
            raise DocumentError(400, "EMPTY_FILE", "空の資料は登録できません。")
        if len(content) > MAX_DOCUMENT_SIZE_BYTES:
            raise DocumentError(400, "FILE_TOO_LARGE", "資料ファイルは10MB以下にしてください。")

        document_id = str(uuid4())
        stored_filename = f"{uuid4()}{extension}"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        destination = self._storage_dir / stored_filename
        try:
            destination.write_bytes(content)
        except OSError as error:
            raise DocumentError(500, "DOCUMENT_SAVE_FAILED", "資料の保存に失敗しました。") from error

        now = datetime.now(timezone.utc)
        document = ProjectDocument(
            id=document_id,
            project_id=project_id,
            filename=filename,
            stored_filename=stored_filename,
            content_type=upload.content_type or "application/octet-stream",
            size_bytes=len(content),
            status="uploaded",
            rag_sync_status="not_started",
            uploaded_by=user.user_id,
            created_at=now,
            updated_at=now,
        )
        self._documents.setdefault(project_id, []).append(document)

        # Local registration is separate from later Open WebUI synchronization.
        processing = document.model_copy(update={"status": "processing", "updated_at": datetime.now(timezone.utc)})
        self._replace(processing)
        ready = processing.model_copy(update={"status": "ready", "updated_at": datetime.now(timezone.utc)})
        self._replace(ready)
        return ready

    async def sync_document(self, project_id: str, document_id: str, project_name: str) -> ProjectDocument:
        document = self.get_document(project_id, document_id)
        if document is None:
            raise DocumentError(404, "DOCUMENT_NOT_FOUND", "指定された資料が見つかりません。")
        if document.rag_sync_status == "synced":
            raise DocumentError(409, "DOCUMENT_ALREADY_SYNCED", "資料はすでにKnowledgeへ同期されています。")

        pending = document.model_copy(
            update={
                "rag_sync_status": "pending",
                "rag_sync_error": None,
                "error_message": None,
                "updated_at": datetime.now(timezone.utc),
            }
        )
        self._replace(pending)
        try:
            await self._open_webui_client.health()
            knowledge_id = self._knowledge_ids.get(project_id)
            if knowledge_id:
                knowledge = await self._open_webui_client.get_knowledge(knowledge_id)
            else:
                knowledge = await self._open_webui_client.create_knowledge(
                    f"{project_name} ({project_id})"
                )
                self._knowledge_ids[project_id] = knowledge.knowledge_id

            file_path = self._storage_dir / pending.stored_filename
            try:
                content = file_path.read_bytes()
            except OSError as error:
                raise DocumentError(500, "FILE_UPLOAD_FAILED", "開発用資料ファイルを読み込めません。") from error

            processing = pending.model_copy(
                update={"rag_sync_status": "processing", "updated_at": datetime.now(timezone.utc)}
            )
            self._replace(processing)
            open_webui_file = await self._open_webui_client.upload_file(
                pending.filename, content, pending.content_type
            )
            processing = processing.model_copy(
                update={
                    "openwebui_file_id": open_webui_file.file_id,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            self._replace(processing)
            file_status = await self._open_webui_client.get_file_processing_status(
                open_webui_file.file_id
            )
            if file_status != "completed":
                raise DocumentError(502, "FILE_PROCESSING_FAILED", "Open WebUIの資料処理に失敗しました。")
            await self._open_webui_client.add_file_to_knowledge(
                knowledge.knowledge_id, open_webui_file.file_id
            )
            synced = processing.model_copy(
                update={
                    "rag_sync_status": "synced",
                    "rag_synced_at": datetime.now(timezone.utc),
                    "rag_sync_error": None,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            self._replace(synced)
            return synced
        except DocumentError as error:
            self._mark_sync_failed(pending, error.message)
            raise
        except Exception as error:
            code = getattr(error, "code", "OPENWEBUI_SYNC_FAILED")
            message = getattr(error, "message", "資料のKnowledge同期に失敗しました。")
            self._mark_sync_failed(pending, message)
            raise DocumentError(502, code, message) from error

    def _replace(self, updated_document: ProjectDocument) -> None:
        documents = self._documents[updated_document.project_id]
        index = next(index for index, item in enumerate(documents) if item.id == updated_document.id)
        documents[index] = updated_document

    def _mark_sync_failed(self, document: ProjectDocument, message: str) -> None:
        current = self.get_document(document.project_id, document.id) or document
        self._replace(
            current.model_copy(
                update={
                    "rag_sync_status": "failed",
                    "rag_sync_error": message,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
        )


def development_upload_dir() -> Path:
    return Path(os.getenv("DOCUMENT_UPLOAD_DIR", "/app/data/uploads"))
