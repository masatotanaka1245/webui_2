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
    const error = new Error(`HTTP ${response.status}`);
    error.status = response.status;
    throw error;
  }
  return response.json();
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
        <button class="action-card" data-placeholder="資料一覧は次の実装で追加します。"><strong>資料一覧</strong><span>資料の確認・アップロード</span></button>
        <button class="action-card" data-placeholder="案件内チャットは次の実装で追加します。"><strong>案件内チャット</strong><span>新規チャットとスレッド管理</span></button>
      </nav>
      <p id="placeholder-message" class="assistive-message">資料一覧と案件内チャットは準備中です。</p>
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

function route() {
  const match = location.hash.match(/^#\/projects\/([^/]+)$/);
  if (match) return renderProjectHome(match[1]);
  return renderProjectList();
}

window.addEventListener("hashchange", route);
route();
