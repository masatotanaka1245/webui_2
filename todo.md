# 開発タスク

更新日: 2026-07-12

## Now

- [ ] P0の案件UI/UXとOpen WebUI公開API契約を検証・確定する
  - 完了条件: 案件一覧、案件ホーム、案件内チャット、案件資料一覧、チャットスレッド一覧のワイヤーフレームを確定する。`readme.md` の公開API検証項目について、対象固定バージョンで可否・認証方式・入出力・エラー・ID対応を確認し、採用範囲を更新する。

## Next

- [ ] P0の業務APIとポータルの基盤を実装する
  - 完了条件: `backend` と `portal` の採用技術、案件一覧・案件ホーム・案件権限確認のAPIスキーマ、認証/利用者ID対応を確定し、最小画面を実装する。

- [ ] Docker開発環境の雛形を追加する
  - 完了条件: `infra/compose.dev.yaml`、`backend/Dockerfile`、`portal/Dockerfile` を追加し、Dockerだけで開発用サービスを起動できる。

- [ ] DockerなしWindows配布の最小ランチャーを実装する
  - 完了条件: 専用venvの導入、Ollama/Open WebUIヘルスチェック、業務API起動、二重起動防止を行うPowerShellスクリプトを用意する。

## Blocked

- なし
