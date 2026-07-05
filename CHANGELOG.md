# 変更履歴 (Changelog)

本ファイルの記法は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に、
バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準じます。

## [Unreleased]

### Added
- GitHub コミュニティ標準ファイル: Issue / Pull Request テンプレート、
  `CODE_OF_CONDUCT.md`、`SECURITY.md`、`CITATION.cff`、本 `CHANGELOG.md`。
- `.editorconfig` / `.clang-format` によるコードスタイルの機械化。
- 数値単体テスト(Clarke/Park 変換の可逆性、定常解の解析値照合など)。
- MkDocs サイトを GitHub Pages へ自動デプロイするワークフロー。
- 共通コア (`common/`) の切り出しによる重複ソースの共有化。
- 英語版 README (`README.en.md`)。

### Changed
- CI に警告昇格 (`-Wall -Wextra`)・`clang-format` 検査・Sanitizer ジョブを追加。
- `.gitignore` の `build/` を `build*/` に拡張。

### Removed
- 作業残骸ファイル(`sim_viewer_updated.py` 各所、`voltage_output.imag.png`)。

## [0.1.0] - 2025

### Added
- 5 モデル構成 (`01`〜`05`) の初期公開。FOC 基本・PWM 駆動・EPS 機構・
  センサーレス制御・統合モデル。
- 共通理論ドキュメント (`docs/`)、CTest スモークテスト、
  GitHub Actions による 5 モデル × 2 OS のビルド/テストマトリクス。
