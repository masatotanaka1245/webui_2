# 開発時のエラー対応FAQ

更新日: 2026-07-12

## DockerがDocker Desktopへ接続できない

**症状**: `permission denied while trying to connect to the docker API` が表示される。

**確認**:

```sh
docker version
docker ps
```

**対処**: Docker Desktopが起動済みか、実行ユーザーがDockerソケットへ接続できるかを確認する。コンテナを削除・初期化する前に、対象ボリュームと必要データを確認する。

## Open WebUIが初回起動のまま待受を開始しない

**症状**: ログにHugging Faceからの埋め込みモデル取得が表示され、`/health` が待受前のままになる。

**原因**: 既定の埋め込みモデルをダウンロードしようとしている。

**対処**: Ollamaの埋め込みモデルを使うよう、以下を設定する。

```text
RAG_EMBEDDING_ENGINE=ollama
RAG_EMBEDDING_MODEL=mxbai-embed-large:latest
RAG_OLLAMA_BASE_URL=http://host.docker.internal:11434
```

WindowsでPython版を動かす場合は、`RAG_OLLAMA_BASE_URL` に `http://127.0.0.1:11434` を設定する。事前に `ollama pull mxbai-embed-large:latest` を実行する。

## Open WebUIコンテナからOllamaへ接続できない

**症状**: モデル一覧が空、またはTool/会話がOllama接続エラーになる。

**確認**:

```sh
ollama list
docker exec webui_2-open-webui python -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:11434/api/tags').status)"
```

**対処**: Dockerコンテナでは `OLLAMA_BASE_URL=http://host.docker.internal:11434` を設定する。WindowsのPython版では `OLLAMA_BASE_URL=http://127.0.0.1:11434` を設定する。Ollamaが起動済みで、`gemma4:e2b` が存在することを確認する。

## `/api/models` が401になる

**症状**: Open WebUIへ未認証で `/api/models` を呼ぶと `401 Unauthorized` になる。

**原因**: Open WebUIの通常の認証動作である。

**対処**: 初回はブラウザで管理者アカウントを作成する。API確認では認証済みセッションまたは適切なAPI認証を使う。未認証401をOllama接続障害として扱わない。

## Open WebUI更新後にログイン状態または画面が不安定になる

**確認**: 固定しているOpen WebUIバージョン、`WEBUI_SECRET_KEY`、ブラウザキャッシュ、更新ログ、データバックアップを確認する。

**対処**:

1. 更新前にOpen WebUIデータをバックアップする。
2. `WEBUI_SECRET_KEY` を更新前後で同じ値に保つ。
3. ブラウザを強制再読み込みする。
4. ステージングでログイン、Ollama、Knowledge、OpenAPI Tool、会話ストリームを確認してから本番へ反映する。

## DockerなしWindowsでOpen WebUIと業務アプリを起動できない

**確認順**:

1. `ollama list` で `gemma4:e2b` と `mxbai-embed-large:latest` を確認する。
2. `open-webui serve` 後に `http://127.0.0.1:8080/health` を確認する。
3. 業務アプリ専用venvが有効で、`http://127.0.0.1:8000/health` が応答することを確認する。
4. `start-webui2.ps1` の `OPEN_WEBUI_COMMAND`、ポート、ログ、PIDを確認する。

**再発防止**: Open WebUI用と業務アプリ用のPython環境を混在させず、ランチャーで起動済みプロセスを検出して二重起動を防ぐ。
