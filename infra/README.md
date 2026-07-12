# ローカル Open WebUI 環境

Ollama はホスト側で動かし、Open WebUI は Docker で動かす開発用構成です。Open WebUI本体はプロジェクトに含めず、検証済みの公式リリース `v0.9.2` を利用します。

```sh
docker compose -f infra/compose.yaml up -d
```

Open WebUI は `http://localhost:3000` で開きます。初回に作成するアカウントが管理者になります。

この構成はホストの Ollama に `host.docker.internal:11434` で接続します。既定の会話モデルとして、Open WebUI のモデル選択画面で `gemma4:e2b` を選択してください。

Knowledge/RAG の埋め込みには、ホストに導入済みの `mxbai-embed-large:latest` を使います。初回起動時に Hugging Face から埋め込みモデルをダウンロードする必要はありません。

WindowsでDockerを使わずに起動する方法、バージョン更新、データの扱いは [Open WebUI と業務ポータルの管理方針](../docs/runtime_management.md) を参照してください。

停止:

```sh
docker compose -f infra/compose.yaml down
```

データを含めて完全に削除する場合だけ、次を実行します。

```sh
docker compose -f infra/compose.yaml down -v
```
