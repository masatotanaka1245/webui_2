const API_BASE_URL = "http://localhost:8000/api/v1";
const app = document.querySelector("#app");

function formatDate(value) {
  return new Intl.DateTimeFormat("ja-JP", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function statusLabel(status) {
  const labels = {
    planning: "計画中",
    active: "進行中",
    completed: "完了",
    on_hold: "保留",
  };
  return labels[status] ?? status;
}

function setView(html) {
  app.innerHTML = html;
}

async function fetchJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw await responseError(response);
  }
  return response.json();
}

async function responseError(response) {
  let message = `HTTP ${response.status}`;
  try {
    const body = await response.json();
    message = body.error?.message ?? message;
  } catch (_) {
    // A safe generic message is used if the API has no JSON error body.
  }
  const error = new Error(message);
  error.status = response.status;
  return error;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  }[character]));
}

function formatBytes(sizeBytes) {
  if (sizeBytes < 1024) return `${sizeBytes} B`;
  if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} KB`;
  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
}

function documentStatusLabel(status) {
  return { uploaded: "登録済み", processing: "処理中", ready: "利用可能", failed: "失敗" }[status] ?? status;
}

function ragStatusLabel(status) {
  return { not_started: "未開始", pending: "同期準備中", processing: "同期中", synced: "同期済み", failed: "同期失敗" }[status] ?? status;
}

function projectCard(project) {
  return `
    <article class="project-card">
      <div class="card-heading">
        <div>
          <p class="eyebrow">${project.code}</p>
          <h2>${project.name}</h2>
        </div>
        <span class="status status-${project.status}">${statusLabel(project.status)}</span>
      </div>
      <dl class="project-metadata">
        <div><dt>所在地</dt><dd>${project.location}</dd></div>
        <div><dt>期間</dt><dd>${project.period}</dd></div>
        <div><dt>資料</dt><dd>${project.document_count} 件</dd></div>
        <div><dt>チャット</dt><dd>${project.chat_thread_count} 件</dd></div>
        <div><dt>最終更新</dt><dd>${formatDate(project.updated_at)}</dd></div>
      </dl>
      <a class="button" href="#/projects/${project.id}">案件ホームを開く</a>
    </article>`;
}

async function renderProjectList() {
  setView(`<section class="page-heading"><p class="eyebrow">案件</p><h1>案件一覧</h1><p>操作する案件を選択してください。</p></section><p class="state">案件を読み込み中です…</p>`);
  try {
    const data = await fetchJson("/projects");
    if (data.items.length === 0) {
      setView(`<section class="page-heading"><p class="eyebrow">案件</p><h1>案件一覧</h1></section><section class="state-panel"><h2>案件がありません</h2><p>案件作成機能は次の実装で追加します。</p></section>`);
      return;
    }
    setView(`
      <section class="page-heading"><p class="eyebrow">案件</p><h1>案件一覧</h1><p>固定開発データを表示しています。</p></section>
      <section class="project-grid">${data.items.map(projectCard).join("")}</section>
    `);
  } catch (error) {
    setView(`<section class="state-panel error"><h1>案件一覧を表示できません</h1><p>APIへ接続できないか、応答に問題があります。</p><p class="error-detail">状態: ${error.status ?? "接続エラー"}</p><button class="button" onclick="location.reload()">再読み込み</button></section>`);
  }
}

function recentList(items, emptyText) {
  if (!items.length) return `<p class="empty-copy">${emptyText}</p>`;
  return `<ul class="recent-list">${items.map((item) => `<li><strong>${item.name ?? item.title}</strong><span>${formatDate(item.updated_at)}</span></li>`).join("")}</ul>`;
}

async function renderProjectHome(projectId) {
  setView(`<p class="state">案件ホームを読み込み中です…</p>`);
  try {
    const project = await fetchJson(`/projects/${projectId}`);
    setView(`
      <a class="back-link" href="#/projects">← 案件一覧へ戻る</a>
      <section class="project-home-heading">
        <div><p class="eyebrow">${project.code}</p><h1>${project.name}</h1></div>
        <span class="status status-${project.status}">${statusLabel(project.status)}</span>
      </section>
      <p class="overview">${project.overview}</p>
      <dl class="project-metadata home-metadata">
        <div><dt>所在地</dt><dd>${project.location}</dd></div>
        <div><dt>期間</dt><dd>${project.period}</dd></div>
        <div><dt>資料</dt><dd>${project.document_count} 件</dd></div>
        <div><dt>チャットスレッド</dt><dd>${project.chat_thread_count} 件</dd></div>
      </dl>
      <nav class="action-grid" aria-label="案件操作">
        <a class="action-card" href="#/projects/${project.id}/documents"><strong>資料一覧</strong><span>資料の確認・アップロード</span></a>
        <button class="action-card" data-placeholder="案件内チャットは次の実装で追加します。"><strong>案件内チャット</strong><span>新規チャットとスレッド管理</span></button>
      </nav>
      <p id="placeholder-message" class="assistive-message">案件内チャットは準備中です。</p>
      <section class="detail-grid">
        <section class="detail-panel"><h2>最近の資料</h2>${recentList(project.recent_documents, "最近の資料はありません。")}</section>
        <section class="detail-panel"><h2>最近のチャット</h2>${recentList(project.recent_chats, "最近のチャットはありません。")}</section>
      </section>
    `);
    document.querySelectorAll("[data-placeholder]").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelector("#placeholder-message").textContent = button.dataset.placeholder;
      });
    });
  } catch (error) {
    if (error.status === 404) {
      setView(`<section class="state-panel"><h1>案件が見つかりません</h1><p>指定された案件IDは存在しません。</p><a class="button" href="#/projects">案件一覧へ戻る</a></section>`);
      return;
    }
    setView(`<section class="state-panel error"><h1>案件ホームを表示できません</h1><p>APIへ接続できないか、応答に問題があります。</p><p class="error-detail">状態: ${error.status ?? "接続エラー"}</p><a class="button" href="#/projects">案件一覧へ戻る</a></section>`);
  }
}

function documentRow(projectId, document) {
  const error = document.error_message
    ? `<p class="document-error">エラー: ${escapeHtml(document.error_message)}</p>`
    : "";
  const syncError = document.rag_sync_error
    ? `<p class="document-error">同期エラー: ${escapeHtml(document.rag_sync_error)}</p>`
    : "";
  const canSync = document.rag_sync_status !== "synced";
  const syncButton = canSync
    ? `<button class="button sync-button" data-project-id="${projectId}" data-document-id="${document.id}">${document.rag_sync_status === "failed" ? "同期を再実行" : "Knowledge同期"}</button>`
    : `<span class="sync-date">同期日時: ${document.rag_synced_at ? formatDate(document.rag_synced_at) : "-"}</span>`;
  return `
    <tr>
      <td><strong>${escapeHtml(document.filename)}</strong>${error}${syncError}</td>
      <td>${escapeHtml(document.content_type)}</td>
      <td>${formatBytes(document.size_bytes)}</td>
      <td>${formatDate(document.created_at)}</td>
      <td><span class="status status-${document.status}">${documentStatusLabel(document.status)}</span></td>
      <td><span class="status status-rag-${document.rag_sync_status}">${ragStatusLabel(document.rag_sync_status)}</span><div class="sync-action">${syncButton}</div></td>
    </tr>`;
}

async function renderDocuments(projectId) {
  setView(`<p class="state">資料一覧を読み込み中です…</p>`);
  try {
    const [project, documents] = await Promise.all([
      fetchJson(`/projects/${projectId}`),
      fetchJson(`/projects/${projectId}/documents`),
    ]);
    setView(`
      <a class="back-link" href="#/projects/${project.id}">← 案件ホームへ戻る</a>
      <section class="project-home-heading">
        <div><p class="eyebrow">${project.code}</p><h1>案件資料一覧</h1><p>${project.name}</p></div>
        <span class="status status-${project.status}">${statusLabel(project.status)}</span>
      </section>
      <section class="detail-panel upload-panel">
        <h2>資料をアップロード</h2>
        <p>対応形式: PDF、TXT、Markdown、CSV。1ファイル10MBまでです。</p>
        <form id="document-upload-form">
          <label class="file-picker" for="document-file">ファイルを選択<input id="document-file" name="file" type="file" accept=".pdf,.txt,.md,.csv" required /></label>
          <button class="button" type="submit">アップロード</button>
        </form>
        <p id="upload-status" class="assistive-message">最初のKnowledge同期時に、案件用Knowledgeを自動作成します。</p>
      </section>
      <section class="detail-panel">
        <h2>登録済み資料</h2>
        <div id="document-list">${renderDocumentList(project.id, documents.items)}</div>
      </section>
    `);
    bindUploadForm(projectId);
    bindSyncButtons(projectId);
  } catch (error) {
    if (error.status === 404) {
      setView(`<section class="state-panel"><h1>案件が見つかりません</h1><p>指定された案件IDは存在しません。</p><a class="button" href="#/projects">案件一覧へ戻る</a></section>`);
      return;
    }
    setView(`<section class="state-panel error"><h1>資料一覧を表示できません</h1><p>${escapeHtml(error.message)}</p><a class="button" href="#/projects/${projectId}">案件ホームへ戻る</a></section>`);
  }
}

function renderDocumentList(projectId, documents) {
  if (!documents.length) {
    return `<section class="empty-state"><h3>資料がありません</h3><p>上のフォームから案件資料を登録してください。</p></section>`;
  }
  return `<div class="table-scroll"><table><thead><tr><th>ファイル名</th><th>種別</th><th>サイズ</th><th>登録日時</th><th>処理状態</th><th>RAG同期</th></tr></thead><tbody>${documents.map((document) => documentRow(projectId, document)).join("")}</tbody></table></div>`;
}

function bindUploadForm(projectId) {
  const form = document.querySelector("#document-upload-form");
  const status = document.querySelector("#upload-status");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submit = form.querySelector("button");
    submit.disabled = true;
    status.textContent = "アップロード中です…";
    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents`, {
        method: "POST",
        body: new FormData(form),
      });
      if (!response.ok) throw await responseError(response);
      const uploadedDocument = await response.json();
      status.textContent = `アップロードが完了しました。処理状態: ${documentStatusLabel(uploadedDocument.status)} / RAG同期: ${ragStatusLabel(uploadedDocument.rag_sync_status)}`;
      form.reset();
      const data = await fetchJson(`/projects/${projectId}/documents`);
      document.querySelector("#document-list").innerHTML = renderDocumentList(projectId, data.items);
      bindSyncButtons(projectId);
    } catch (error) {
      status.textContent = `アップロードに失敗しました: ${error.message}`;
    } finally {
      submit.disabled = false;
    }
  });
}

function bindSyncButtons(projectId) {
  document.querySelectorAll(".sync-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const status = document.querySelector("#upload-status");
      button.disabled = true;
      status.textContent = "Knowledge同期中です…";
      try {
        const response = await fetch(`${API_BASE_URL}/projects/${projectId}/documents/${button.dataset.documentId}/sync`, {
          method: "POST",
        });
        if (!response.ok) throw await responseError(response);
        const synced = await response.json();
        status.textContent = `Knowledge同期が完了しました。状態: ${ragStatusLabel(synced.rag_sync_status)}`;
        const data = await fetchJson(`/projects/${projectId}/documents`);
        document.querySelector("#document-list").innerHTML = renderDocumentList(projectId, data.items);
        bindSyncButtons(projectId);
      } catch (error) {
        status.textContent = `Knowledge同期に失敗しました: ${error.message}`;
        button.disabled = false;
      }
    });
  });
}

function route() {
  const documentMatch = location.hash.match(/^#\/projects\/([^/]+)\/documents$/);
  if (documentMatch) return renderDocuments(documentMatch[1]);
  const match = location.hash.match(/^#\/projects\/([^/]+)$/);
  if (match) return renderProjectHome(match[1]);
  return renderProjectList();
}

window.addEventListener("hashchange", route);
route();
