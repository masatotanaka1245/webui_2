# 開発タスク

更新日: 2026-07-12

## Now

- [ ] P0の業務APIとポータルの基盤・契約を確定する
  - 完了条件: `backend` と `portal` の採用技術、案件一覧・案件詳細・案件権限確認のAPIスキーマ、認証/利用者ID対応、P0画面ワイヤーフレームを `readme.md` または必要な詳細設計に反映する。

## Next

- [ ] Docker開発環境の雛形を追加する
  - 完了条件: `infra/compose.dev.yaml`、`backend/Dockerfile`、`portal/Dockerfile` を追加し、Dockerだけで開発用サービスを起動できる。

- [ ] DockerなしWindows配布の最小ランチャーを実装する
  - 完了条件: 専用venvの導入、Ollama/Open WebUIヘルスチェック、業務API起動、二重起動防止を行うPowerShellスクリプトを用意する。

- [ ] OpenAPI Toolの案件ACL契約を設計する
  - 完了条件: 入出力、認可、拒否レスポンス、監査イベント、非同期 `job_id` の契約とテスト観点を定義する。

## Blocked

- なし
