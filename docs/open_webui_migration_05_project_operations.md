# 新プロジェクトの Markdown 運用方針

## 採用したリポジトリ構成

```text
new-openwebui-project/
├── readme.md                # プロジェクト仕様
├── agents.md                # 開発方針
├── todo.md                  # 開発タスク管理
├── troubleshoot.md          # 開発時のエラー対応FAQ
├── docs/
│   └── ...                  # 移行調査・承認済み詳細設計の証跡
├── backend/                 # FastAPI / worker
├── portal/                  # 独自業務フロントエンド
├── infra/
└── openwebui/               # Functions・設定例・Tool登録手順のみ
```

## Markdownの責務

| ファイル | 記載すること | 記載しないこと |
| --- | --- | --- |
| `readme.md` | 全体仕様、構成、対応機能、実行・配布の概要 | 作業履歴、秘密情報 |
| `agents.md` | Plan → Do → Check/Debug → Act、編集・検証・ログ・セキュリティの規則 | 日々のタスク、障害ログ |
| `todo.md` | Now 1件、Next 最大3件、各項目の完了条件、Blocked | 完了済みの作業日誌、調査メモの全文 |
| `troubleshoot.md` | 症状、原因、確認手順、対処、再発防止のFAQ | パスワード、トークン、個人情報、DBダンプ |
| `docs/` | 移行調査・承認済み詳細設計の証跡。必要な場合だけ `readme.md` からリンクする | 一時的な作業ログ、日々のタスク、障害の一次記録 |

## TODO.md テンプレート

```md
# 開発タスク

更新日: YYYY-MM-DD

## Now

- [ ] OpenAPI Tool の案件ACL契約を確定する
  - 完了条件: OpenAPIスキーマ、認可ルール、拒否時レスポンス、テスト観点を `readme.md` または必要な詳細設計に記載する。

## Next

- [ ] Open WebUI Knowledge の日本語PDF検索をPoC評価する
- [ ] CSV安全集計APIの最小実装を作る
- [ ] 非同期PDF生成ジョブの入出力を設計する

## Blocked

- なし
```

## 作業サイクル

1. **Plan**: `readme.md` と `todo.md` を確認し、変更種別、対象、成功条件を決める。
2. **Do**: 小さく実装し、Open WebUI本体ではなく外部境界を優先する。
3. **Check / Debug**: API契約、認可、ジョブ失敗、RAG根拠、更新互換性を確認する。
4. **Act**: 仕様変更を `readme.md`、再発事項を `troubleshoot.md`、次の未完了を `todo.md` に反映する。詳細設計が必要な場合だけ `docs/` を更新する。

## 詳細設計を追加する条件

- `readme.md` に収まらないAPIスキーマ、データモデル、セキュリティ要件、移行判断を確定した場合だけ `docs/` に追加する。
- 追加した詳細設計は、目的が分かるよう `readme.md` からリンクする。
