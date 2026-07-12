# 開発方針

更新日: 2026-07-12

## プロジェクトの原則

- Open WebUIは改造・forkしない。会話、モデル接続、Knowledge/RAG、標準ファイル管理を担う外部基盤として使う。
- 独自に開発するのは、案件・権限・資料/CSV・成果物・進捗を扱う業務ポータル、業務API、ワーカーである。Open WebUIのチャットUIを複製・埋込・DOM操作しない。
- Open WebUIとの業務連携は、公開設定、OpenAPI Tool、通常のHTTP APIだけで行う。内部DB、非公開API、Cookie、DOM/CSSを契約にしない。
- 業務APIはポータルとToolの両方から受けた利用者、案件、操作を再認可する。クライアントの `project_id`、ロール、SQLを信頼しない。

## 開発・配布の原則

- 開発、CI、再現テストはDocker Composeを正本とする。業務API/ワーカーは同一の固定Python依存で動かす。
- 利用者のWindows PCではDockerを要求しない。既存のOllamaと `open-webui serve` に、専用venvまたは配布用実行ファイルの業務アプリを追加する。
- Open WebUIのPython環境に業務アプリの依存を混在させない。
- Open WebUI本体はDocker/Pythonとも検証済みの固定バージョンを使う。更新は業務機能変更と分け、DockerとWindowsで回帰確認してから行う。
- 秘密情報、個人情報、実行時データ、モデル、DBダンプ、ログをGitへ追加しない。

## 作業サイクル

1. **Plan**: `readme.md` の仕様と `todo.md` の完了条件を確認し、変更範囲を決める。
2. **Do**: 小さく実装する。Open WebUI本体ではなく、ポータル/API/Toolの境界へ実装する。
3. **Check / Debug**: テスト、認可、ジョブ失敗、Tool契約、Windows配布、Open WebUI更新互換性を確認する。
4. **Act**: タスクを `todo.md`、再発防止を `troubleshoot.md`、仕様変更を `readme.md` へ反映する。

## Markdownの管理規則

| ファイル | 正本として管理する内容 |
| --- | --- |
| `agents.md` | この開発方針、編集・検証・安全性の規則 |
| `readme.md` | プロジェクト仕様、構成、対応機能、起動・配布の概要 |
| `todo.md` | 実行中の作業1件、次の作業最大3件、完了条件、ブロック事項 |
| `troubleshoot.md` | 症状、原因、確認手順、対処、再発防止のFAQ |

- 上記4ファイルに該当する内容は、新しいMarkdownを増やさず該当ファイルへ追記・更新する。
- 新しいMarkdownは原則として追加しない。仕様・設計判断は `readme.md` に簡潔に統合する。
- `docs/` に残る移行調査4件は一時的な参照資料であり、日々の作業では更新しない。P0仕様の確定後に、必要事項を `readme.md` へ取り込み、削除する。
