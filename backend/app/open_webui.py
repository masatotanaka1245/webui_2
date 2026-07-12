import asyncio
import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class KnowledgeReference:
    knowledge_id: str
    name: str


@dataclass(frozen=True)
class FileReference:
    file_id: str
    name: str
    processing_status: str


@dataclass(frozen=True)
class ChatReference:
    chat_id: str
    title: str


class OpenWebUIClientError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class OpenWebUIClient(ABC):
    """Boundary for documented Open WebUI HTTP API operations only."""

    @abstractmethod
    async def health(self) -> None: ...

    @abstractmethod
    async def get_knowledge(self, knowledge_id: str) -> KnowledgeReference: ...

    @abstractmethod
    async def create_knowledge(self, name: str) -> KnowledgeReference: ...

    @abstractmethod
    async def upload_file(self, name: str, content: bytes, content_type: str) -> FileReference: ...

    @abstractmethod
    async def add_file_to_knowledge(self, knowledge_id: str, file_id: str) -> None: ...

    @abstractmethod
    async def get_file_processing_status(self, file_id: str) -> str: ...

    @abstractmethod
    async def run_chat(self, knowledge_id: str, message: str) -> str: ...

    @abstractmethod
    async def list_threads(self, knowledge_id: str) -> list[ChatReference]: ...


class MockOpenWebUIClient(OpenWebUIClient):
    """Deterministic development adapter; it performs no Open WebUI I/O."""

    async def health(self) -> None:
        return None

    async def get_knowledge(self, knowledge_id: str) -> KnowledgeReference:
        return KnowledgeReference(knowledge_id=knowledge_id, name="Mock Knowledge")

    async def create_knowledge(self, name: str) -> KnowledgeReference:
        return KnowledgeReference(knowledge_id=f"mock-knowledge-{name}", name=name)

    async def upload_file(self, name: str, content: bytes, content_type: str) -> FileReference:
        return FileReference(file_id=f"mock-file-{uuid4()}", name=name, processing_status="completed")

    async def add_file_to_knowledge(self, knowledge_id: str, file_id: str) -> None:
        return None

    async def get_file_processing_status(self, file_id: str) -> str:
        return "completed"

    async def run_chat(self, knowledge_id: str, message: str) -> str:
        return "Mock Open WebUI response. Live RAG is not enabled yet."

    async def list_threads(self, knowledge_id: str) -> list[ChatReference]:
        return [ChatReference(chat_id="mock-chat-1", title="Mock thread")]


class LiveOpenWebUIClient(OpenWebUIClient):
    """Public Open WebUI API adapter. Credentials stay in process memory only."""

    def __init__(self) -> None:
        self._base_url = (
            os.getenv("OPENWEBUI_INTERNAL_BASE_URL") or os.getenv("OPENWEBUI_BASE_URL") or ""
        ).rstrip("/")
        self._api_key = os.getenv("OPENWEBUI_API_KEY") or None
        self._email = os.getenv("OPENWEBUI_DEV_EMAIL") or None
        self._password = os.getenv("OPENWEBUI_DEV_PASSWORD") or None
        self._jwt: str | None = None

    async def health(self) -> None:
        status, _ = await self._request("GET", "/health", auth=False, operation="OPENWEBUI_UNAVAILABLE")
        if status != 200:
            raise OpenWebUIClientError("OPENWEBUI_UNAVAILABLE", "Open WebUIへ接続できません。")

    async def get_knowledge(self, knowledge_id: str) -> KnowledgeReference:
        status, payload = await self._request(
            "GET", f"/api/v1/knowledge/{knowledge_id}", operation="KNOWLEDGE_CREATE_FAILED"
        )
        if status != 200 or not payload.get("id"):
            raise OpenWebUIClientError("KNOWLEDGE_CREATE_FAILED", "案件用Knowledgeを確認できません。")
        return KnowledgeReference(knowledge_id=payload["id"], name=payload.get("name", ""))

    async def create_knowledge(self, name: str) -> KnowledgeReference:
        status, payload = await self._request(
            "POST",
            "/api/v1/knowledge/create",
            json_body={"name": name, "description": "Business portal project knowledge"},
            operation="KNOWLEDGE_CREATE_FAILED",
        )
        if status not in (200, 201) or not payload.get("id"):
            raise OpenWebUIClientError("KNOWLEDGE_CREATE_FAILED", "案件用Knowledgeの作成に失敗しました。")
        return KnowledgeReference(knowledge_id=payload["id"], name=payload.get("name", name))

    async def upload_file(self, name: str, content: bytes, content_type: str) -> FileReference:
        boundary = f"----portal{uuid4().hex}"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode() + content + f"\r\n--{boundary}--\r\n".encode()
        status, payload = await self._request(
            "POST",
            "/api/v1/files/",
            body=body,
            content_type=f"multipart/form-data; boundary={boundary}",
            operation="FILE_UPLOAD_FAILED",
        )
        if status not in (200, 201) or not payload.get("id"):
            raise OpenWebUIClientError("FILE_UPLOAD_FAILED", "Open WebUIへの資料登録に失敗しました。")
        return FileReference(
            file_id=payload["id"],
            name=payload.get("filename", {}).get("name", name) if isinstance(payload.get("filename"), dict) else name,
            processing_status="pending",
        )

    async def get_file_processing_status(self, file_id: str) -> str:
        status, payload = await self._request(
            "GET",
            f"/api/v1/files/{file_id}/process/status",
            operation="FILE_PROCESSING_FAILED",
        )
        processing_status = payload.get("status") if status == 200 else None
        if processing_status is None:
            raise OpenWebUIClientError("FILE_PROCESSING_FAILED", "資料処理状態を取得できません。")
        return processing_status

    async def add_file_to_knowledge(self, knowledge_id: str, file_id: str) -> None:
        status, _ = await self._request(
            "POST",
            f"/api/v1/knowledge/{knowledge_id}/file/add",
            json_body={"file_id": file_id},
            operation="KNOWLEDGE_ATTACH_FAILED",
        )
        if status not in (200, 201):
            raise OpenWebUIClientError("KNOWLEDGE_ATTACH_FAILED", "資料をKnowledgeへ関連付けできません。")

    async def run_chat(self, knowledge_id: str, message: str) -> str:
        raise OpenWebUIClientError("CHAT_NOT_IMPLEMENTED", "RAGチャットはまだ実装していません。")

    async def list_threads(self, knowledge_id: str) -> list[ChatReference]:
        raise OpenWebUIClientError("THREADS_NOT_IMPLEMENTED", "スレッド一覧はまだ実装していません。")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        auth: bool = True,
        json_body: dict | None = None,
        body: bytes | None = None,
        content_type: str | None = None,
        operation: str,
    ) -> tuple[int, dict]:
        if not self._base_url:
            raise OpenWebUIClientError("OPENWEBUI_UNAVAILABLE", "Open WebUIの接続先が設定されていません。")
        headers: dict[str, str] = {"Accept": "application/json"}
        if auth:
            headers["Authorization"] = f"Bearer {await self._credential()}"
        if json_body is not None:
            body = json.dumps(json_body).encode()
            content_type = "application/json"
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(
            f"{self._base_url}{path}", data=body, method=method, headers=headers
        )
        try:
            status, response_body = await asyncio.to_thread(self._open, request)
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                raise OpenWebUIClientError("OPENWEBUI_AUTH_FAILED", "Open WebUIの認証に失敗しました。") from error
            raise OpenWebUIClientError(operation, "Open WebUI APIがエラーを返しました。") from error
        except (urllib.error.URLError, OSError) as error:
            raise OpenWebUIClientError("OPENWEBUI_UNAVAILABLE", "Open WebUIへ接続できません。") from error
        try:
            payload = json.loads(response_body) if response_body else {}
        except json.JSONDecodeError:
            payload = {}
        return status, payload

    @staticmethod
    def _open(request: urllib.request.Request) -> tuple[int, bytes]:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read()

    async def _credential(self) -> str:
        if self._api_key:
            return self._api_key
        if self._jwt:
            return self._jwt
        if not self._email or not self._password:
            raise OpenWebUIClientError("OPENWEBUI_AUTH_FAILED", "Open WebUIの開発用認証情報が設定されていません。")
        login = urllib.request.Request(
            f"{self._base_url}/api/v1/auths/signin",
            data=json.dumps({"email": self._email, "password": self._password}).encode(),
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        try:
            _, body = await asyncio.to_thread(self._open, login)
            token = json.loads(body).get("token")
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, json.JSONDecodeError) as error:
            raise OpenWebUIClientError("OPENWEBUI_AUTH_FAILED", "Open WebUIの認証に失敗しました。") from error
        if not token:
            raise OpenWebUIClientError("OPENWEBUI_AUTH_FAILED", "Open WebUIの認証トークンを取得できません。")
        self._jwt = token
        return token


def create_open_webui_client() -> OpenWebUIClient:
    if os.getenv("OPENWEBUI_CLIENT_MODE", "mock").lower() == "live":
        return LiveOpenWebUIClient()
    return MockOpenWebUIClient()
