# Contributing

このリポジトリ（`bldc-foc-sim`）への貢献に興味を持っていただきありがとうございます。
本プロジェクトは BLDC/PMSM の FOC を 5 つのモデル（`01`〜`05`）で段階的に学ぶ
教材リポジトリです。各モデルは独立してビルド・実行できます。

## 貢献の流れ

1. リポジトリを **Fork** し、`main` からフィーチャーブランチを切る。
2. 変更を加える。
3. 触れたモデルがビルドでき、スモークテストが通ることを確認する（下記）。
4. 変更内容と理由を明記して Pull Request を作成する。

## ビルドとテスト

各モデルは個別の CMake プロジェクトです（共通の実行ファイル名 `BrushlessDCMotor`）。

```bash
# 例: モデル 02 をビルドしてテスト
cmake -S 02-foc-pwm-drive -B 02-foc-pwm-drive/build -DCMAKE_BUILD_TYPE=Release
cmake --build 02-foc-pwm-drive/build --config Release
ctest --test-dir 02-foc-pwm-drive/build -C Release --output-on-failure
```

`ctest` は最小のスモークテスト（短時間実行で `RESULT` 行を NaN/Inf なく出力するか）を
実行します。CI（GitHub Actions）でも 5 モデル × Ubuntu/Windows のマトリクスで
同じ手順が自動実行されます。

> 注: 全モデルが同じターゲット名 `BrushlessDCMotor` を使うため、5 モデルを
> 1 つの CMake ツリーにまとめてビルドすることはできません。**モデルごとに
> 個別に** configure / build / test してください。

## コードスタイル

- C++20、コンパイラ拡張は無効（`CMAKE_CXX_EXTENSIONS OFF`）
- インデントは半角スペース 4、タブ禁止
- 計算結果を返す関数には `[[nodiscard]]`
- 生ポインタによる所有を避け、RAII を用いる
- 整形はリポジトリ同梱の `.clang-format` に準拠（`clang-format -i <file>` で自動整形）。
  CI（`lint` ジョブ）が逸脱を検査します。
- 高警告レベル（`-Wall -Wextra` / `/W4`）でクリーンにビルドできること。CI は
  `-DBLDC_WARNINGS_AS_ERRORS=ON` で警告をエラー扱いにします。

## モデル間で共有されるファイル

各モデルは自己完結（`src/` に全ソースを保持）ですが、**どのモデルでも本来同一**の
ユーティリティが物理的に複製されています。これらはモデル間でバイト一致を保つ必要が
あり、CI（`consistency` ジョブ）が一致を検査します。

対象ファイル（各モデルの `src/` 配下）:

- `motor_vector_conv.hpp` / `motor_vector_conv.cpp`（Clarke / Park 変換・中点変調）
- `csv_verifier.hpp` / `csv_verifier.cpp`（CSV 回帰照合）

いずれか 1 つを変更した場合は、**全モデルへ同一内容を反映**してください。ローカルでは
次のコマンドで一致を確認できます（リポジトリのルートで実行）。

```bash
bash tests/check_shared_files.sh
```

## パラメータ変更時の回帰参照更新

`src/sim_params.hpp`（または `eps_sim_params.hpp`）のモータ・制御パラメータを
変更した場合は、リファレンス CSV を再生成して PR に含めてください。

```bash
./BrushlessDCMotor
cp data/sim_output.csv data/motor_log.csv
```

## Issue 報告

GitHub Issue に以下を添えてください。

- OS とコンパイラのバージョン
- 実行した正確なコマンドライン
- コンソール出力の全文
