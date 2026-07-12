from datetime import datetime, timezone
from uuid import uuid4

from .documents import DocumentError, DocumentService
from .open_webui import OpenWebUIClient, OpenWebUIClientError
from .schemas import ChatCitation, ChatMessage, ChatThread, DevelopmentUser


RAG_NOT_READY_MESSAGE = "RAGに利用できる資料がありません。資料画面でKnowledge同期を実行してください。"


class ChatService:
    """Development-only project chat store; Open WebUI calls stay behind the client."""

    def __init__(self, document_service: DocumentService, open_webui_client: OpenWebUIClient):
        self._document_service = document_service
        self._open_webui_client = open_webui_client
        self._threads: dict[str, list[ChatThread]] = {}

    def list_threads(self, project_id: str) -> list[ChatThread]:
        return sorted(self._threads.get(project_id, []), key=lambda thread: thread.updated_at, reverse=True)

    def create_thread(self, project_id: str, title: str | None, user: DevelopmentUser) -> ChatThread:
        now = datetime.now(timezone.utc)
        thread = ChatThread(
            id=str(uuid4()),
            project_id=project_id,
            title=(title or "新規チャット").strip() or "新規チャット",
            created_by=user.user_id,
            created_at=now,
            updated_at=now,
        )
        self._threads.setdefault(project_id, []).append(thread)
        return thread

    def get_thread(self, project_id: str, thread_id: str) -> ChatThread | None:
        return next((thread for thread in self._threads.get(project_id, []) if thread.id == thread_id), None)

    async def add_message(
        self, project_id: str, thread_id: str, content: str, model_id: str
    ) -> ChatThread:
        thread = self.get_thread(project_id, thread_id)
        if thread is None:
            raise DocumentError(404, "CHAT_THREAD_NOT_FOUND", "指定されたチャットスレッドが見つかりません。")
        knowledge_id = self._document_service.knowledge_id_for_project(project_id)
        synced_documents = [
            document
            for document in self._document_service.list_documents(project_id)
            if document.rag_sync_status == "synced"
        ]
        if not knowledge_id or not synced_documents:
            raise DocumentError(409, "RAG_NOT_READY", RAG_NOT_READY_MESSAGE)

        now = datetime.now(timezone.utc)
        user_message = ChatMessage(
            id=str(uuid4()), thread_id=thread.id, role="user", content=content,
            model_id=model_id, created_at=now,
        )
        self._replace(thread.model_copy(update={"messages": [*thread.messages, user_message], "updated_at": now}))
        current = self.get_thread(project_id, thread_id)
        assert current is not None
        try:
            completion = await self._open_webui_client.chat_with_knowledge(
                project_id=project_id,
                knowledge_id=knowledge_id,
                messages=[{"role": message.role, "content": message.content} for message in current.messages],
                model_id=model_id,
            )
        except OpenWebUIClientError as error:
            raise DocumentError(502, error.code, error.message) from error
        assistant_message = ChatMessage(
            id=str(uuid4()), thread_id=current.id, role="assistant", content=completion.answer,
            citations=[ChatCitation(**citation.__dict__) for citation in completion.citations],
            model_id=completion.model_id, created_at=datetime.now(timezone.utc),
        )
        result = current.model_copy(
            update={"messages": [*current.messages, assistant_message], "updated_at": assistant_message.created_at}
        )
        self._replace(result)
        return result

    def _replace(self, updated: ChatThread) -> None:
        threads = self._threads[updated.project_id]
        index = next(index for index, item in enumerate(threads) if item.id == updated.id)
        threads[index] = updated
