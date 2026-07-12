# DockerなしWindows PCへの配布・起動計画

更新日: 2026-07-12  
状態: 決定

## 方針

Dockerは開発、CI、再現テストだけで使用する。利用者のWindows PCではDockerを要求せず、既存のOllamaとOpen WebUI（`open-webui serve`）に、独立して配布する業務ポータル/APIを加える。

Open WebUIのPython環境へ業務アプリのライブラリを追加しない。業務アプリは専用の仮想環境または配布済み実行ファイルで動かし、Open WebUIとの連携はHTTP/OpenAPI Toolに限る。

## 配布する構成

```text
webui2-release/
├── portal/                 # ビルド済みの静的フロントエンド
├── backend/                # FastAPI業務APIとワーカー
├── requirements.lock       # 検証済みのPython依存
├── wheels/                 # オフライン導入用wheel群（必要な配布形態で同梱）
├── config.example.env      # 端末ごとの設定テンプレート
├── install-webui2.ps1      # 専用仮想環境の作成・依存導入
├── start-webui2.ps1        # Open WebUIと業務アプリの起動
├── stop-webui2.ps1         # 業務アプリの停止
└── logs/                   # Git管理しない実行ログ
```

Node.jsは利用者PCに要求しない。`portal/` は開発時にビルドし、静的ファイルとして配布する。P0ではFastAPIがこの静的ファイルを配信してもよく、利用者PCで起動する業務アプリを最小の1サービスにできる。

非同期ワーカーが必要になった時点で、APIプロセスとワーカープロセスを別に起動する。起動ランチャーが両方の状態を確認する。

## 端末で必要なもの

| 必須 | 役割 | 備考 |
| --- | --- | --- |
| Windows | 利用者端末 | Dockerは不要 |
| Ollama | `gemma4:e2b` と埋め込みモデルの実行 | 既存導入を利用する |
| Open WebUI | 会話・Knowledge/RAG | 既存の `open-webui serve` を利用する |
| Python 3.11 | 業務APIの専用仮想環境 | Open WebUIと別のvenvを作る。Pythonの実行パスはランチャー設定で指定可能にする |
| ブラウザ | ポータルとOpen WebUIの利用 | Chrome/Edgeを想定 |

## 1回で起動するランチャー

利用者は `start-webui2.ps1` だけを実行する。ランチャーは以下を行う。

1. Ollamaの `http://127.0.0.1:11434/api/tags` を確認する。未起動または必要モデルがない場合は、操作案内を表示して終了する。
2. Open WebUIの `http://127.0.0.1:8080/health` を確認する。未起動なら、設定された `OPEN_WEBUI_COMMAND` で `open-webui serve` を別プロセスで起動する。
3. Open WebUIのヘルスチェック成功を待つ。起動済みの場合は再起動・二重起動しない。
4. 業務APIを `127.0.0.1:8000` で起動し、ヘルスチェックを待つ。P1以降はワーカーも起動・監視する。
5. 業務ポータルを `http://127.0.0.1:8000`、Open WebUIを `http://127.0.0.1:8080` で開く。
6. 各プロセスのPID、開始時刻、ログファイルを記録する。停止は `stop-webui2.ps1` が業務アプリだけを安全に停止する。

Open WebUIは既存の利用者環境で管理されるため、停止スクリプトは原則としてOpen WebUIとOllamaを停止しない。

## 設定とポート

| 項目 | 標準値 | 管理方法 |
| --- | --- | --- |
| Ollama | `http://127.0.0.1:11434` | `config.env` |
| Open WebUI | `http://127.0.0.1:8080` | `config.env` |
| 業務ポータル/API | `http://127.0.0.1:8000` | `config.env` |
| Open WebUI起動コマンド | `open-webui serve` | `OPEN_WEBUI_COMMAND`。PATHにない端末ではvenv内の実行ファイルを設定する |
| 業務データ | `%LOCALAPPDATA%\webui2\data` | 端末固有。Git管理しない |
| ログ | `%LOCALAPPDATA%\webui2\logs` | 端末固有。機微情報をマスクする |

ポータル/APIは利用者PCではローカルインターフェースだけへ待受させる。LAN公開や外部公開は別の運用設計が必要であり、標準配布に含めない。

## 開発と配布の対応

| 開発/CI（Docker） | Windows配布版（Dockerなし） |
| --- | --- |
| `backend` コンテナでFastAPI・テストを実行 | 同じ固定Python依存を専用venvへ導入してFastAPIを実行 |
| `portal` コンテナで静的ファイルをビルド | ビルド済み静的ファイルを同梱 |
| ComposeでDB/キュー/ストレージを再現 | P0では端末内の軽量構成を採用するか、接続先を設定で渡す。P1着手前にデータ保管先を確定する |
| Composeのログとヘルスチェック | ランチャーのPID管理、ログ、HTTPヘルスチェック |

DockerとWindows配布版は、同じAPI契約・テスト・固定依存から作る。Windows用にOpen WebUIの内部DBや画面へ依存する実装は追加しない。

## 実装順序

1. P0の業務APIを、DockerとWindows専用venvの双方で起動できるPythonパッケージとして実装する。
2. ポータルを静的ビルドできるようにし、業務APIから配信する。
3. `config.example.env`、インストール、起動、停止のPowerShellスクリプトを作成する。
4. Dockerを導入していないWindows PCで、Ollama → Open WebUI → 業務ポータルの新規セットアップと二重起動防止を受入テストする。
5. P1以降のDB、ワーカー、成果物保存を追加する前に、端末ローカルに置くデータとサーバー側へ置くデータを決定する。

## 受入条件

- GitHubのリリース成果物を展開し、DockerなしWindows PCで手順どおりに導入できる。
- `start-webui2.ps1` が、既に起動しているOpen WebUIを再起動せず、未起動なら起動できる。
- Ollama、Open WebUI、業務APIの各障害を、ヘルスチェックとログから区別できる。
- 業務ポータルからOpen WebUIへ移動し、OpenAPI Tool経由の業務API呼出しを行える。
- Open WebUIを更新しても、公開された設定・OpenAPI契約が保たれる限り、業務ポータルの再ビルドを不要とする。
