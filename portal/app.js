const API_ORIGIN = "http://localhost:8000";
const API_BASE_URL = `${API_ORIGIN}/api/v1`;
const app = document.querySelector("#app");

const projectExtras = {
  "project-central-library": { field: "公共施設改修", todo: "設計資料の確認", todoStatus: "進行中", csvCount: 1 },
  "project-river-monitoring": { field: "環境調査", todo: "観測項目の整理", todoStatus: "未着手", csvCount: 0 },
};

const workspace = {
  projects: [], selectedId: location.hash.replace("#/projects/", ""), project: null, documents: [],
  threads: [], activeThreadId: null, activeTab: "overview", previewDocumentId: null,
  answerMode: "通常", health: null, evidenceMessage: "",
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[character]));
}

function formatDate(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("ja-JP", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function formatBytes(sizeBytes) {
  if (sizeBytes < 1024) return `${sizeBytes} B`;
  if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} KB`;
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

function statusLabel(status) {
  return { planning: "計画中", active: "進行中", completed: "完了", on_hold: "保留" }[status] ?? status;
}

function documentStatusLabel(status) {
  return { uploaded: "登録済み", processing: "処理中", ready: "利用可能", failed: "失敗" }[status] ?? status;
}

function ragStatusLabel(status) {
  return { not_started: "未開始", pending: "同期準備中", processing: "同期中", synced: "同期済み", failed: "同期失敗" }[status] ?? status;
}

async function responseError(response) {
  let message = `HTTP ${response.status}`;
  try { message = (await response.json()).error?.message ?? message; } catch (_) { /* safe fallback */ }
  const error = new Error(message); error.status = response.status; return error;
}

async function fetchJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) throw await responseError(response);
  return response.json();
}

async function postJson(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  if (!response.ok) throw await responseError(response);
  return response.json();
}

async function health() {
  const response = await fetch(`${API_ORIGIN}/health`);
  if (!response.ok) throw await responseError(response);
  return response.json();
}

function setView(html) { app.innerHTML = html; }

function projectExtra(projectId) {
  return projectExtras[projectId] ?? { field: "未設定", todo: "TODO未登録", todoStatus: "未着手", csvCount: 0 };
}

function projectList() {
  if (!workspace.projects.length) return `<p class="empty-copy">案件がありません。</p>`;
  return workspace.projects.map((project) => {
    const extra = projectExtra(project.id);
    const selected = project.id === workspace.selectedId ? " selected-project" : "";
    const pending = Math.max(0, project.document_count - (workspace.project?.id === project.id ? workspace.project.rag_synced_document_count : 0));
    return `<button class="project-list-item${selected}" data-project-id="${project.id}">
      <span class="project-list-top"><strong>${escapeHtml(project.name)}</strong><span class="status status-${project.status}">${statusLabel(project.status)}</span></span>
      <span class="project-code">${escapeHtml(project.code)}</span>
      <span class="project-list-meta">${escapeHtml(extra.field)} / ${escapeHtml(project.location)}</span>
      <span class="project-list-meta">更新 ${formatDate(project.updated_at)}</span>
      <span class="project-list-badges"><span>未処理資料 ${pending}件</span><span>TODO: ${escapeHtml(extra.todo)}</span></span>
    </button>`;
  }).join("");
}

function workspaceShell(center, right) {
  return `<section class="workspace" aria-label="案件統合ワークスペース">
    <aside class="workspace-left"><div class="panel-title"><div><p class="eyebrow">案件</p><h2>案件一覧</h2></div><span>${workspace.projects.length} 件</span></div><div id="project-list">${projectList()}</div></aside>
    <main class="workspace-center">${center}</main>
    <aside class="workspace-right">${right}</aside>
  </section>`;
}

function loadingWorkspace() {
  setView(workspaceShell(`<section class="workspace-state"><h1>案件を読み込み中です…</h1><p>中央ワークスペースを準備しています。</p></section>`, `<section class="workspace-state"><h2>AIチャット</h2><p>読み込み中です…</p></section>`));
}

function errorWorkspace(error) {
  setView(workspaceShell(`<section class="workspace-state error"><h1>案件情報を表示できません</h1><p>${escapeHtml(error.message)}</p><button class="button" data-action="reload">再読み込み</button></section>`, `<section class="workspace-state error"><h2>AIチャット</h2><p>backendへの接続を確認してください。</p></section>`));
  bindWorkspaceEvents();
}

function tabs() {
  const items = [
    ["overview", "概要"], ["documents", "資料"], ["csv", "CSVデータ"], ["notes", "資料メモ"],
    ["comments", "コメント"], ["faq", "FAQ"], ["members", "メンバー"], ["jobs", "成果物・ジョブ"],
  ];
  if (workspace.previewDocumentId) {
    const document = workspace.documents.find((item) => item.id === workspace.previewDocumentId);
    if (document) items.splice(2, 0, ["preview", document.filename]);
  }
  return `<nav class="workspace-tabs" aria-label="案件ワークスペースのタブ">${items.map(([id, label]) => `<button class="workspace-tab ${workspace.activeTab === id ? "active-tab" : ""}" data-tab="${id}">${escapeHtml(label)}</button>`).join("")}</nav>`;
}

function metric(label, value) { return `<div class="metric"><dt>${label}</dt><dd>${value}</dd></div>`; }

function overviewPanel(project) {
  const extra = projectExtra(project.id);
  return `<section class="tab-panel"><div class="project-heading"><div><p class="eyebrow">${escapeHtml(project.code)}</p><h1>${escapeHtml(project.name)}</h1><p>${escapeHtml(project.overview)}</p></div><span class="status status-${project.status}">${statusLabel(project.status)}</span></div>
    <dl class="metrics-grid">${metric("分野", escapeHtml(extra.field))}${metric("所在地", escapeHtml(project.location))}${metric("期間", escapeHtml(project.period))}${metric("資料", `${project.document_count} 件`)}${metric("CSV", `${extra.csvCount} 件`)}${metric("スレッド", `${workspace.threads.length} 件`)}${metric("進行中TODO", `${escapeHtml(extra.todo)} / ${extra.todoStatus}`)}${metric("最近の更新", formatDate(project.updated_at))}</dl>
    <section class="compact-section"><h2>最近の更新</h2>${project.recent_documents.length || project.recent_chats.length ? `<ul class="activity-list">${[...project.recent_documents, ...project.recent_chats].slice(0, 5).map((item) => `<li><strong>${escapeHtml(item.name ?? item.title)}</strong><span>${formatDate(item.updated_at)}</span></li>`).join("")}</ul>` : `<p class="empty-copy">最近の更新はありません。</p>`}</section></section>`;
}

function documentRow(document) {
  const isSelected = document.id === workspace.previewDocumentId ? " selected-document" : "";
  const syncButton = document.rag_sync_status === "synced"
    ? `<span class="sync-date">同期済み ${formatDate(document.rag_synced_at)}</span>`
    : `<button class="minor-button" data-action="sync" data-document-id="${document.id}">${document.rag_sync_status === "failed" ? "同期を再実行" : "Knowledge同期"}</button>`;
  return `<tr class="${isSelected}" data-action="preview" data-document-id="${document.id}"><td><strong>${escapeHtml(document.filename)}</strong>${document.error_message ? `<p class="document-error">${escapeHtml(document.error_message)}</p>` : ""}${document.rag_sync_error ? `<p class="document-error">${escapeHtml(document.rag_sync_error)}</p>` : ""}</td><td>v1</td><td>${formatDate(document.created_at)}</td><td>${escapeHtml(document.uploaded_by)}</td><td><span class="status status-${document.status}">${documentStatusLabel(document.status)}</span></td><td><span class="status status-rag-${document.rag_sync_status}">${ragStatusLabel(document.rag_sync_status)}</span><div>${syncButton}</div></td></tr>`;
}

function documentsPanel() {
  return `<section class="tab-panel"><div class="tab-heading"><div><h1>資料</h1><p>案件資料を登録し、Knowledge同期状態を確認します。</p></div><span>${workspace.documents.length} 件</span></div>
    <form id="document-upload-form" class="upload-bar"><input id="document-file" name="file" type="file" accept=".pdf,.txt,.md,.csv" required><button class="button" type="submit">資料をアップロード</button><span id="upload-status">PDF / TXT / Markdown / CSV、10MBまで</span></form>
    <div class="table-scroll">${workspace.documents.length ? `<table><thead><tr><th>ファイル名</th><th>版</th><th>登録日時</th><th>登録者</th><th>処理</th><th>RAG同期</th></tr></thead><tbody>${workspace.documents.map(documentRow).join("")}</tbody></table>` : `<section class="empty-state"><h2>資料がありません</h2><p>上の操作から最初の資料を登録してください。</p></section>`}</div>
    ${workspace.evidenceMessage ? `<p class="evidence-notice">${escapeHtml(workspace.evidenceMessage)}</p>` : ""}</section>`;
}

function previewPanel() {
  const document = workspace.documents.find((item) => item.id === workspace.previewDocumentId);
  if (!document) return documentsPanel();
  const isPdf = document.filename.toLowerCase().endsWith(".pdf");
  return `<section class="tab-panel preview-panel"><div class="tab-heading"><div><p class="eyebrow">資料プレビュー</p><h1>${escapeHtml(document.filename)}</h1><p>${isPdf ? "PDF.js連携は次工程で追加します。" : "現在は資料メタデータと選択イベントを表示しています。"}</p></div><button class="minor-button" data-tab="documents">資料一覧へ戻る</button></div><dl class="metrics-grid">${metric("種別", escapeHtml(document.content_type))}${metric("サイズ", formatBytes(document.size_bytes))}${metric("処理", documentStatusLabel(document.status))}${metric("RAG", ragStatusLabel(document.rag_sync_status))}</dl><div class="preview-placeholder"><span aria-hidden="true">▧</span><strong>${isPdf ? "PDFページプレビュー領域" : "資料プレビュー領域"}</strong><p>根拠資料クリックからこのタブを開くイベント境界を実装済みです。</p></div></section>`;
}

function futurePanel(title, description, layout) {
  return `<section class="tab-panel"><div class="tab-heading"><div><h1>${title}</h1><p>${description}</p></div><span class="implementation-label">未実装</span></div>${layout}</section>`;
}

function centerContent() {
  if (!workspace.project) return `<section class="workspace-state"><h1>案件を選択してください</h1></section>`;
  let panel;
  switch (workspace.activeTab) {
    case "documents": panel = documentsPanel(); break;
    case "preview": panel = previewPanel(); break;
    case "csv": panel = futurePanel("CSVデータ", "CSV取込・プレビューの実装前レイアウトです。", `<section class="split-placeholder"><div><h2>CSVファイル一覧</h2><p>案件別のCSV / TSVを表示します。</p></div><div><h2>表形式プレビュー</h2><p>列名、行番号、Text-to-SQL結果、AI指定行ハイライトをここに表示します。</p></div></section>`); break;
    case "notes": panel = futurePanel("資料メモ", "Markdownで育てる作業用成果品です。", `<section class="split-placeholder"><div><h2>資料メモ一覧</h2><p>版・更新日時・TODO状態を管理します。</p><ul class="todo-lanes"><li>進行中（主レーンは1件）</li><li>未着手</li><li>検証中</li><li>完了</li><li>保留</li></ul></div><div><h2>編集 / プレビュー</h2><p>Markdown編集エリアとプレビューを配置します。</p></div></section>`); break;
    case "comments": panel = futurePanel("コメント", "案件の検討事項と関係者コメントを記録します。", `<p class="empty-copy">コメントAPIの実装後に時系列表示を追加します。</p>`); break;
    case "faq": panel = futurePanel("FAQ", "再利用する質問と回答を案件単位で管理します。", `<p class="empty-copy">FAQの登録・Knowledge同期はP2候補です。</p>`); break;
    case "members": panel = futurePanel("メンバー", "案件ロールとアクセス権を表示します。", `<p class="empty-copy">開発中は固定ユーザーを使用しています。ACL実装時に置き換えます。</p>`); break;
    case "jobs": panel = futurePanel("成果物・ジョブ", "帳票・CSVなどの成果物と非同期ジョブを追跡します。", `<p class="empty-copy">ジョブID、状態、再実行、失敗理由を追加予定です。</p>`); break;
    default: panel = overviewPanel(workspace.project);
  }
  return `${tabs()}${panel}`;
}

function citations(message) {
  if (!message.citations?.length) return "";
  return `<ul class="citation-list">${message.citations.map((citation) => `<li><button class="citation-link" data-action="citation" data-reference="${escapeHtml(citation.reference ?? "")}"><span>根拠資料</span>${escapeHtml(citation.source_name)}</button></li>`).join("")}</ul>`;
}

function messages() {
  const thread = workspace.threads.find((item) => item.id === workspace.activeThreadId);
  if (!thread) return `<section class="empty-state chat-empty"><h2>スレッドを選択してください</h2><p>新規チャットから会話を開始できます。</p></section>`;
  if (!thread.messages.length) return `<section class="empty-state chat-empty"><h2>質問を入力してください</h2><p>案件Knowledgeに同期済みの資料を対象に回答します。</p></section>`;
  return thread.messages.map((message) => `<article class="chat-message ${message.role === "assistant" ? "assistant-message" : "user-message"}"><p class="message-role">${message.role === "assistant" ? "AI" : "あなた"}</p><div class="message-content">${escapeHtml(message.content).replace(/\n/g, "<br>")}</div>${citations(message)}</article>`).join("");
}

function chatPanel() {
  const project = workspace.project;
  if (!project) return `<section class="workspace-state"><h2>AIチャット</h2><p>案件を選択してください。</p></section>`;
  const ragReady = Boolean(project.openwebui_knowledge_id) && project.rag_synced_document_count > 0;
  const mode = workspace.health?.open_webui_client === "live" ? "Live" : "Mock";
  return `<section class="chat-panel"><header class="chat-panel-header"><div><p class="eyebrow">案件内AIチャット</p><h2>${escapeHtml(project.name)}</h2><p class="chat-context">Knowledge: ${project.openwebui_knowledge_id ? "設定済み" : "未作成"} / 同期資料: ${project.rag_synced_document_count}件 / ${mode}</p></div><button class="icon-button" data-action="collapse-chat" aria-label="チャットパネルを折りたたむ">›</button></header>
    <div class="thread-controls"><select id="thread-select" aria-label="チャットスレッド"><option value="">スレッドを選択</option>${workspace.threads.map((thread) => `<option value="${thread.id}" ${thread.id === workspace.activeThreadId ? "selected" : ""}>${escapeHtml(thread.title)}</option>`).join("")}</select><button class="minor-button" data-action="new-thread">＋ 新規</button></div>
    ${ragReady ? "" : `<div class="rag-warning compact"><strong>RAGに利用できる資料がありません。</strong><button class="text-button" data-tab="documents">資料画面でKnowledge同期を実行</button></div>`}
    <div class="message-list">${messages()}</div>
    <details class="chat-details"><summary>詳細な処理状態</summary><p>モデル: gemma4:e2b / 回答モード: ${workspace.answerMode} / Open WebUI: ${mode}</p></details>
    <form id="chat-form" class="chat-composer"><p id="chat-status">${ragReady ? "入力内容を案件資料と照合して回答します。" : "資料同期後に送信できます。"}</p><div><select id="answer-mode" aria-label="回答モード"><option>通常</option><option>図解</option><option>報告書</option></select><textarea id="chat-input" required placeholder="案件について質問してください。" ${ragReady && workspace.activeThreadId ? "" : "disabled"}></textarea></div><div class="composer-actions"><button class="minor-button" type="button" disabled>送信停止</button><button class="button" type="submit" ${ragReady && workspace.activeThreadId ? "" : "disabled"}>送信</button></div></form></section>`;
}

function renderWorkspace() {
  setView(workspaceShell(centerContent(), chatPanel()));
  bindWorkspaceEvents();
}

async function loadProject(projectId) {
  workspace.selectedId = projectId;
  workspace.activeTab = "overview"; workspace.previewDocumentId = null; workspace.activeThreadId = null; workspace.evidenceMessage = "";
  location.hash = `#/projects/${projectId}`;
  loadingWorkspace();
  try {
    const [project, documents, threads, healthInfo] = await Promise.all([
      fetchJson(`/projects/${projectId}`), fetchJson(`/projects/${projectId}/documents`),
      fetchJson(`/projects/${projectId}/chat-threads`), health(),
    ]);
    workspace.project = project; workspace.documents = documents.items; workspace.threads = threads.items; workspace.health = healthInfo;
    renderWorkspace();
  } catch (error) { errorWorkspace(error); }
}

async function refreshProject() {
  if (workspace.selectedId) await loadProject(workspace.selectedId);
}

function openEvidence(reference) {
  const document = workspace.documents.find((item) => item.id === reference || item.openwebui_file_id === reference);
  workspace.evidenceMessage = document ? `根拠資料「${document.filename}」を開きました。` : "根拠の資料メタデータはまだポータルに登録されていません。資料一覧を確認してください。";
  workspace.previewDocumentId = document?.id ?? null;
  workspace.activeTab = document ? "preview" : "documents";
  renderWorkspace();
}

function bindWorkspaceEvents() {
  document.querySelectorAll("[data-project-id]").forEach((element) => element.addEventListener("click", () => loadProject(element.dataset.projectId)));
  document.querySelectorAll("[data-tab]").forEach((element) => element.addEventListener("click", () => { workspace.activeTab = element.dataset.tab; renderWorkspace(); }));
  document.querySelectorAll('[data-action="preview"]').forEach((element) => element.addEventListener("click", (event) => {
    if (event.target.closest("button")) return;
    workspace.previewDocumentId = element.dataset.documentId; workspace.activeTab = "preview"; renderWorkspace();
  }));
  document.querySelectorAll('[data-action="sync"]').forEach((element) => element.addEventListener("click", () => syncDocument(element.dataset.documentId)));
  document.querySelectorAll('[data-action="citation"]').forEach((element) => element.addEventListener("click", () => openEvidence(element.dataset.reference)));
  document.querySelector('[data-action="new-thread"]')?.addEventListener("click", createThread);
  document.querySelector("#thread-select")?.addEventListener("change", async (event) => {
    workspace.activeThreadId = event.target.value || null;
    if (workspace.activeThreadId) await loadThread(workspace.activeThreadId); else renderWorkspace();
  });
  document.querySelector("#document-upload-form")?.addEventListener("submit", uploadDocument);
  document.querySelector("#chat-form")?.addEventListener("submit", sendMessage);
  document.querySelector("#answer-mode")?.addEventListener("change", (event) => { workspace.answerMode = event.target.value; });
  document.querySelector('[data-action="reload"]')?.addEventListener("click", refreshProject);
  document.querySelector('[data-action="collapse-chat"]')?.addEventListener("click", () => app.classList.toggle("chat-collapsed"));
}

async function uploadDocument(event) {
  event.preventDefault();
  const form = event.currentTarget; const status = document.querySelector("#upload-status"); const button = form.querySelector("button");
  button.disabled = true; status.textContent = "アップロード中です…";
  try {
    const response = await fetch(`${API_BASE_URL}/projects/${workspace.selectedId}/documents`, { method: "POST", body: new FormData(form) });
    if (!response.ok) throw await responseError(response);
    status.textContent = "アップロードしました。資料一覧を更新します。"; form.reset(); await refreshProject();
  } catch (error) { status.textContent = `アップロード失敗: ${error.message}`; button.disabled = false; }
}

async function syncDocument(documentId) {
  workspace.evidenceMessage = "Knowledge同期中です…"; renderWorkspace();
  try { await postJson(`/projects/${workspace.selectedId}/documents/${documentId}/sync`, {}); await refreshProject(); }
  catch (error) { workspace.evidenceMessage = `Knowledge同期失敗: ${error.message}`; renderWorkspace(); }
}

async function createThread() {
  try {
    const thread = await postJson(`/projects/${workspace.selectedId}/chat-threads`, { title: "新規チャット" });
    workspace.threads = [thread, ...workspace.threads]; workspace.activeThreadId = thread.id; renderWorkspace();
  } catch (error) { workspace.evidenceMessage = `スレッド作成失敗: ${error.message}`; renderWorkspace(); }
}

async function loadThread(threadId) {
  try {
    const thread = await fetchJson(`/projects/${workspace.selectedId}/chat-threads/${threadId}`);
    workspace.threads = workspace.threads.map((item) => item.id === thread.id ? thread : item); renderWorkspace();
  } catch (error) { workspace.evidenceMessage = `スレッド読込失敗: ${error.message}`; renderWorkspace(); }
}

async function sendMessage(event) {
  event.preventDefault();
  const form = event.currentTarget; const input = document.querySelector("#chat-input"); const status = document.querySelector("#chat-status"); const submit = form.querySelector('[type="submit"]');
  submit.disabled = true; input.disabled = true; status.textContent = "回答を生成中です…";
  try {
    const thread = await postJson(`/projects/${workspace.selectedId}/chat-threads/${workspace.activeThreadId}/messages`, { content: input.value, model_id: "gemma4:e2b" });
    workspace.threads = workspace.threads.map((item) => item.id === thread.id ? thread : item); input.value = ""; renderWorkspace();
  } catch (error) { status.textContent = `回答を取得できませんでした: ${error.message}`; submit.disabled = false; input.disabled = false; }
}

async function boot() {
  loadingWorkspace();
  try {
    const data = await fetchJson("/projects"); workspace.projects = data.items;
    if (!workspace.projects.length) { setView(workspaceShell(`<section class="workspace-state"><h1>案件がありません</h1></section>`, `<section class="workspace-state"><h2>AIチャット</h2><p>案件を作成してください。</p></section>`)); return; }
    if (!workspace.projects.some((project) => project.id === workspace.selectedId)) workspace.selectedId = workspace.projects[0].id;
    await loadProject(workspace.selectedId);
  } catch (error) { errorWorkspace(error); }
}

window.addEventListener("hashchange", () => {
  const projectId = location.hash.replace("#/projects/", "");
  if (projectId && projectId !== workspace.selectedId) loadProject(projectId);
});
boot();
