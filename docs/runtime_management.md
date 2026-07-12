# Open WebUI と業務ポータルの管理方針

更新日: 2026-07-12  
状態: 決定

## 決定

Open WebUI本体と本プロジェクトのソースコードは、別のライフサイクルで管理する。

| 対象 | 管理方法 | このリポジトリに置くもの | 置かないもの |
| --- | --- | --- | --- |
| Open WebUI本体 | 公式DockerイメージまたはPyPIパッケージを、検証済みの固定バージョンで導入する | バージョン、起動設定、接続設定、更新手順 | Open WebUIのソースfork、内部DB、ユーザーデータ、アップロード資料 |
| Ollama | 各端末のローカルランタイムとして導入する | 必要モデル名、動作確認手順 | モデル実体、モデルキャッシュ |
| 業務ポータル | このGitHubリポジトリで開発・版管理する | `portal/`、`backend/`、`infra/`、テスト、設計資料、CI設定 | 環境固有の秘密情報、DBダンプ、実行時データ |
| 業務データ | 業務DB・オブジェクトストレージで管理する | スキーマ、マイグレーション、匿名化されたテストデータ | 本番データ、トークン、鍵 |

この分離により、Open WebUIを更新する場合も、業務ポータルのコードを改変せず、公開設定・OpenAPI Tool・通常のHTTP APIの互換性だけを検証対象にする。

## リポジトリ構成

```text
webui_2/
├── portal/                 # 独自業務フロントエンド（今後追加）
├── backend/                # 業務API・ワーカー（今後追加）
├── infra/                  # Dockerでの開発起動
├── openwebui/              # Python版の固定バージョン・起動設定・更新手順
├── docs/                   # 業務仕様、契約、運用判断
└── .env                    # Git管理しない端末固有設定
```

`openwebui/` はOpen WebUI本体のソース置き場ではない。Docker/Pythonのどちらでも同じバージョンと接続設定を再現するための、依存関係と運用手順の置き場とする。

## 対応する実行方式

### A. Docker を使える端末

- `infra/compose.yaml` で Open WebUI を起動する。
- Open WebUIのデータはDockerボリュームに保持する。
- ホストの Ollama には `host.docker.internal:11434` で接続する。
- イメージは `main` ではなく、検証済みのリリースタグに固定する。

### B. WindowsでDockerを使わない端末

- Python 3.11 の仮想環境を端末ごとに作成する。
- `openwebui/requirements.txt` に固定したOpen WebUIをインストールする。
- Ollamaを同じWindows端末で起動し、`http://127.0.0.1:11434` に接続する。
- 事前に `gemma4:e2b` と `mxbai-embed-large:latest` を `ollama pull` で取得する。
- `DATA_DIR` をリポジトリ外の端末固有ディレクトリへ設定してから `open-webui serve` を実行する。
- 業務ポータル/APIは別プロセスとして起動する。Open WebUIのPython環境に業務アプリの依存関係を混在させない。

PowerShellの概念例:

```powershell
py -3.11 -m venv .venv-openwebui
.\.venv-openwebui\Scripts\Activate.ps1
pip install -r openwebui\requirements.txt
$env:DATA_DIR = "$HOME\webui_2-data\open-webui"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:RAG_EMBEDDING_ENGINE = "ollama"
$env:RAG_EMBEDDING_MODEL = "mxbai-embed-large:latest"
$env:RAG_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:WEBUI_SECRET_KEY = "端末ごとに生成して安全に保管する固定値"
open-webui serve
```

Open WebUI公式のPythonインストール・更新手順は [Quick Start](https://docs.openwebui.com/getting-started/quick-start/) を参照する。

## バージョン固定と更新手順

1. `openwebui/requirements.txt` と `infra/compose.yaml` に、同じ検証済みOpen WebUIバージョンを記録する。
2. Open WebUIの更新は、業務ポータルの機能変更とは別のPull Request/コミットで扱う。
3. 更新候補をステージングで、Docker方式とPython方式の両方で確認する。
4. 更新前にOpen WebUIのデータをバックアップし、リリースノートの破壊的変更を確認する。
5. ログイン、Ollama接続、`gemma4:e2b` の会話、Knowledgeの日本語検索、OpenAPI Tool、会話ストリームを回帰確認する。
6. 合格後にバージョン固定を更新し、Docker/Pythonそれぞれで再現できることを確認する。

Open WebUIは更新時にデータベースマイグレーションを行うことがあるため、バックアップと単一ワーカーでの起動確認を必須にする。詳細は公式の [Updating Open WebUI](https://docs.openwebui.com/getting-started/updating/) を参照する。

## データと秘密情報の扱い

- Open WebUIの `DATA_DIR` とDockerボリュームは端末・環境ごとに管理し、Gitへ追加しない。
- `WEBUI_SECRET_KEY`、業務APIの鍵、DB接続情報は `.env` または安全な秘密情報ストアで渡す。`.env.example` には値を入れない。
- 端末を替えるとき、Git cloneで再現するのは設定・コードのみとする。会話、Knowledge、ユーザー、アップロード資料を移す必要がある場合は、別途バックアップ/移行手順として扱う。
- Docker方式とPython方式で同一のOpen WebUIデータディレクトリを同時に使用しない。

## 直近の実施項目

1. `openwebui/requirements.txt` と `.env.example` を追加し、Python版の最小起動をWindowsで検証する。
2. 業務ポータル/APIの依存関係と起動方法をOpen WebUIから分離して定義する。
3. Open WebUI更新用のステージングチェックリストと、データバックアップ手順を追加する。
