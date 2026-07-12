# 開発タスク

更新日: 2026-07-12

## Now

- [ ] Open WebUI統合用認証を準備し、P0公開APIの認証済み検証を完了する
  - 完了条件: Open WebUI `v0.9.2` の統合用サービスアカウントまたは同等の安全な認証方式を準備し、検証用Knowledge・小テキスト・チャット各1件以内で、`readme.md` の未確認項目を実機確認する。検証データの削除可否を記録する。

## Next

- [ ] P0の業務APIとポータルの基盤を実装する
  - 完了条件: `backend` と `portal` の採用技術、案件一覧・案件ホーム・案件権限確認のAPIスキーマ、認証/利用者ID対応を確定し、最小画面を実装する。

- [ ] Docker開発環境の雛形を追加する
  - 完了条件: `infra/compose.dev.yaml`、`backend/Dockerfile`、`portal/Dockerfile` を追加し、Dockerだけで開発用サービスを起動できる。

- [ ] DockerなしWindows配布の最小ランチャーを実装する
  - 完了条件: 専用venvの導入、Ollama/Open WebUIヘルスチェック、業務API起動、二重起動防止を行うPowerShellスクリプトを用意する。

## Blocked

- オンボーディング未完了で、Open WebUIの初期管理者・APIキーが未設定。既存利用者の管理者権限を勝手に取得・変更しないため、認証済みの書込み検証は保留。
