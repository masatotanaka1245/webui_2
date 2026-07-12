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

    def list_documents(self, project_id: str) -> list[ProjectDocument]:
        return list(self._documents.get(project_id, []))

    def get_document(self, project_id: str, document_id: str) -> ProjectDocument | None:
        return next(
            (document for document in self._documents.get(project_id, []) if document.id == document_id),
            None,
        )

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

        # The mock reproduces the future upload lifecycle without real I/O.
        processing = document.model_copy(update={"status": "processing", "updated_at": datetime.now(timezone.utc)})
        self._replace(processing)
        await self._open_webui_client.upload_file(filename, content)
        ready = processing.model_copy(update={"status": "ready", "updated_at": datetime.now(timezone.utc)})
        self._replace(ready)
        return ready

    def _replace(self, updated_document: ProjectDocument) -> None:
        documents = self._documents[updated_document.project_id]
        index = next(index for index, item in enumerate(documents) if item.id == updated_document.id)
        documents[index] = updated_document


def development_upload_dir() -> Path:
    return Path(os.getenv("DOCUMENT_UPLOAD_DIR", "/app/data/uploads"))
