# bldc-foc-sim

<!-- push 後、下記バッジの <OWNER> を GitHub アカウント/組織名に置き換えて有効化 -->
[![CI](https://github.com/<OWNER>/bldc-foc-sim/actions/workflows/ci.yml/badge.svg)](https://github.com/<OWNER>/bldc-foc-sim/actions/workflows/ci.yml)
[![Docs](https://github.com/<OWNER>/bldc-foc-sim/actions/workflows/docs.yml/badge.svg)](https://github.com/<OWNER>/bldc-foc-sim/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![C++20](https://img.shields.io/badge/C%2B%2B-20-blue.svg)
![CMake](https://img.shields.io/badge/CMake-3.16%2B-064F8C.svg?logo=cmake)

📖 English: [`README.en.md`](README.en.md)

三相ブラシレスモータ (BLDC / PMSM) のベクトル制御 (FOC) と、その応用である
電動パワーステアリング (EPS) を題材にした、C++ / CMake のシミュレーション
教材リポジトリです。

要素技術を一つずつ積み上げていく **5 つのモデル** で構成されており、
順番に読み進めることで FOC・PWM 駆動・EPS 機構・センサーレス制御を
段階的に理解できます。

---

## モデル一覧

| モデル | 内容 | 主な追加要素 |
|--------|------|--------------|
| [`01-foc-ideal-voltage`](01-foc-ideal-voltage/) | FOC 基本 (理想電圧源駆動) | dq 軸 PI 制御・FOC ループ |
| [`02-foc-pwm-drive`](02-foc-pwm-drive/) | 01 + PWM インバータ駆動 | PWM・DC リンク電圧制限 |
| [`03-foc-pwm-eps`](03-foc-pwm-eps/) | 02 + 電動パワーステアリング機構 | コラム・トーションバー・ラック |
| [`04-foc-pwm-sensorless`](04-foc-pwm-sensorless/) | 02 + センサーレス制御 | 誘起電圧オブザーバ + PLL |
| [`05-foc-pwm-eps-sensorless`](05-foc-pwm-eps-sensorless/) | 03 + 04 の統合 | 全要素技術の統合 |

依存関係（読み進める順番）:

```
01 ──▶ 02 ──┬─▶ 03 (EPS 機構) ───┐
            └─▶ 04 (センサーレス) ┴─▶ 05 (統合)
```

各モデルのディレクトリにある `README.md` に、ビルド方法・実行方法・
出力の説明が記載されています。

---

## クイックスタート

どのモデルも「ディレクトリへ移動 → ビルド → 実行」の 3 ステップです。
ビルド手順は全モデル共通です。

```sh
# 1. 対象モデルのディレクトリへ移動
cd 02-foc-pwm-drive

# 2. ビルド (全モデル共通)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

必要環境: C++20 対応コンパイラ、CMake 3.16 以上、Eigen3 3.4 以上。
(Windows では各モデルの `build.ps1` / `run.ps1` でも同じことができます。)

### モデル別の実行例

ビルドすると各モデル直下に実行ファイルが生成されます。`01`・`02`・`04` は
モータ単体の `BrushlessDCMotor`、`03`・`05` はこれに加えて EPS 機構込みの
`EpsGearboxSim` が生成されます (Windows では `.exe`)。

| モデル | 主な実行コマンド | 何が起きるか |
|--------|------------------|--------------|
| `01-foc-ideal-voltage` | `./BrushlessDCMotor --iq_ref 85 --tload 4.3 --span 2.0` | 理想電圧源で FOC 電流ループを実行 |
| `02-foc-pwm-drive` | `./BrushlessDCMotor --iq_ref 85 --vdc 48 --span 2.0` | PWM 駆動。`--midpoint` で電圧利用率拡張 |
| `03-foc-pwm-eps` | `./EpsGearboxSim --tmax 6.0 --ramp 0.3 --span 2.0` | EPS 機構にランプ操舵トルクを与え応答評価 |
| `04-foc-pwm-sensorless` | `./BrushlessDCMotor --iq_ref 85 --span 2.0` | センサーレスでロータ角を推定しつつ駆動 |
| `05-foc-pwm-eps-sensorless` | `./EpsGearboxSim --tmax 6.0 --ramp 0.3 --span 2.0` | センサーレス + EPS 機構の統合実行 |

共通オプション: `--span <s>` (時間)、`--csv_out <path>` / `--no_csv` (CSV 出力)、
`--quiet` (RESULT 行のみ出力)、`--midpoint` / `--decoupling` (機能 ON/OFF)。
`EpsGearboxSim` は `--tmax` (最大操舵トルク) と `--ramp` (ランプ時間) を追加で受け付けます。
オプションの詳細・既定値は各モデルの `README.md` を参照してください。

```sh
# RESULT 行のみを取り出す例 (スクリプト連携用)
./BrushlessDCMotor --quiet
```

---

## テスト・CI

各モデルには CTest による最小スモークテスト（短時間実行で `RESULT` 行を
NaN/Inf なく出力するか）が登録されています。

```sh
cmake -S 02-foc-pwm-drive -B 02-foc-pwm-drive/build -DCMAKE_BUILD_TYPE=Release
cmake --build 02-foc-pwm-drive/build --config Release
ctest --test-dir 02-foc-pwm-drive/build -C Release --output-on-failure
```

GitHub Actions（[`.github/workflows/ci.yml`](.github/workflows/ci.yml)）で、
5 モデル × Ubuntu(GCC)/Windows(MSVC) のマトリクスにより
configure → build → ctest を自動実行します。

> 全モデルが同じターゲット名 `BrushlessDCMotor` を使うため、1 つの CMake
> ツリーにまとめてビルドできません。モデルごとに個別にビルド・テストします。


---

## 共通機能

すべての PWM 駆動モデルは、以下の機能を実行時フラグで切り替えられます
(いずれも既定 OFF)。

| フラグ | 機能 |
|--------|------|
| `--midpoint` | 中点変調 (SVPWM)。電圧利用率を $2/\sqrt{3}$ 倍に拡張 |
| `--decoupling` | dq 軸非干渉制御。軸間結合をフィードフォワードで打ち消す |
| `--iq_step <t> <iq>` | 指定時刻に q 軸電流指令をステップさせ、過渡を発生させる |

---

## 結果の読み取り

### 出力の種類

シミュレーション結果は 2 つの経路で得られます。

| 出力 | 形式 | 内容 |
|------|------|------|
| `RESULT` 行 (標準出力) | 1 行のキー=値 | 定常状態の主要量。`--quiet` でこの行のみ出力し、スクリプト連携に使う |
| `data/*.csv` | 時系列 CSV | 各計算ステップの波形。下表のファイルに分かれる |

`RESULT` 行の主なキー: `omega_ss` (定常回転数)・`iq_ss` / `id_ss` (dq 軸電流)・
`te_ss` (電磁トルク)・`tload`。`02` 以降は `pwm_duty` / `v_rms`、センサーレス
(`04`/`05`) は `angle_err_ss` (推定角度誤差) が加わります。

CSV は生成するモデルが異なります。

| ファイル | 生成モデル | 内容 |
|----------|-----------|------|
| `data/sim_output.csv` | 全モデル | 三相・dq 軸電流、トルク、回転速度、角度 (02 以降はデューティ・相電圧も) |
| `data/pwm_waveform.csv` | 02–05 | 三角波キャリアと比較した PWM パルス列 |
| `data/eps_output.csv` | 03 / 05 | EPS 機構の応答 (トーションバートルク・アシストトルク・ラック推力・変位) |
| `data/verification.csv` | 全モデル | 回帰照合用リファレンス (CI のスモークテストが参照) |

### 結果読み取り用 Python スクリプト (`scripts/`)

まず依存パッケージを入れます (各モデル共通、GUI 系は PyQt6 / matplotlib を使用)。

```sh
pip install -r 02-foc-pwm-drive/scripts/requirements.txt
```

スクリプトは用途で 4 種類に分かれます。モデルによって同梱物が一部異なります。

| 種類 | スクリプト | 用途 | 読む対象 |
|------|-----------|------|----------|
| 波形ビューア (GUI) | `sim_viewer.py` | モータ波形を対話的に表示 | `data/sim_output.csv` |
| 波形ビューア (GUI) | `eps_viewer.py` (03/05) | EPS 機構の応答を表示 | `data/eps_output.csv` |
| 特性スイープ | `tn_sweep.py` | `iq_ref` を振って T-n / I-T / P-T / η-T 特性を描画 | ソルバを複数回実行 |
| 特性スイープ | `motor_characteristics_gui.py` | モータ特性マップ (N/I/P/η vs トルク) を GUI 表示 | ソルバを複数回実行 |
| 特性スイープ | `eps_vcurve_sweep.py` (03/05) | EPS の V カーブ (操舵トルク→アシスト) を掃引 | ソルバを複数回実行 |
| 条件比較 | `compare_modulation.py` | 中点変調・非干渉制御の ON/OFF を 4 条件で比較 | ソルバを条件別に実行 |
| 条件比較 | `compare_decoupling_transient.py` | 非干渉制御の過渡応答を ON/OFF で比較 | ソルバを条件別に実行 |
| 静的プロット | `plot_result.py` (01) | 波形を PNG 画像として保存 | `data/sim_output.csv` |

```sh
# 例: 02 で波形ビューアを開く / 変調条件を比較する
cd 02-foc-pwm-drive
python scripts/sim_viewer.py
python scripts/compare_modulation.py --span 2.0
```

> ビューア (`sim_viewer.py` / `eps_viewer.py`) は既存の CSV をそのまま読みます。
> スイープ・比較系はスクリプト内部でソルバを複数回実行して結果を集計します。

---

## ドキュメント

モータ制御の理論的背景は、リポジトリ共通の [`docs/`](docs/) にまとめて
あります。

```
docs/
├── theory/
│   ├── motor-model.md          モータの電気・機械方程式
│   ├── foc.md                  ベクトル制御 (FOC) の原理
│   ├── coordinate-transform.md Clarke / Park 変換
│   ├── pwm-inverter.md         PWM・三相インバータ・中点変調
│   ├── pi-tuning.md            PI ゲインの極配置設計
│   ├── sensorless.md           誘起電圧オブザーバ + PLL
│   ├── eps.md                  電動パワーステアリングの力学モデル
│   └── functional-safety.md    機能安全 (HARA / ISO 26262)
├── derivations.md              数式の導出
├── glossary.md                 用語集
└── references.md               参考文献
```

---

## ライセンス

本リポジトリは MIT ライセンスで公開されています。詳細はルートの
[`LICENSE`](LICENSE) を参照してください（各モデルディレクトリにも同一の
`LICENSE` を同梱しています）。
