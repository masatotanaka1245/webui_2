from abc import ABC, abstractmethod
from dataclasses import dataclass


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


class OpenWebUIClient(ABC):
    """Boundary for public Open WebUI API operations.

    A live implementation will own authentication and HTTP calls. Routes and UI
    must depend on this interface, never on Open WebUI internals.
    """

    @abstractmethod
    async def create_knowledge(self, name: str) -> KnowledgeReference: ...

    @abstractmethod
    async def upload_file(self, name: str, content: bytes) -> FileReference: ...

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

    async def create_knowledge(self, name: str) -> KnowledgeReference:
        return KnowledgeReference(knowledge_id=f"mock-knowledge-{name}", name=name)

    async def upload_file(self, name: str, content: bytes) -> FileReference:
        return FileReference(file_id=f"mock-file-{name}", name=name, processing_status="completed")

    async def add_file_to_knowledge(self, knowledge_id: str, file_id: str) -> None:
        return None

    async def get_file_processing_status(self, file_id: str) -> str:
        return "completed"

    async def run_chat(self, knowledge_id: str, message: str) -> str:
        return "Mock Open WebUI response. Live RAG is not enabled yet."

    async def list_threads(self, knowledge_id: str) -> list[ChatReference]:
        return [ChatReference(chat_id="mock-chat-1", title="Mock thread")]
