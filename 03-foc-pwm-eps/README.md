# 03 - FOC PWM 電動パワーステアリングモデル

`02` の PWM 駆動モデルに **電動パワーステアリング (EPS) 機構** を追加した
C++ / CMake シミュレーションです。BLDC モータに加えて、ステアリングコラム・
トーションバー・減速ギア・ラックといった機械系をモデル化し、ドライバの操舵に
対するアシスト動作全体を再現します。

> **シリーズ構成**
>
> | モデル | 内容 |
> |--------|------|
> | 01-foc-ideal-voltage | FOC 基本 (理想電圧源駆動) |
> | 02-foc-pwm-drive | 01 + PWM インバータ駆動 |
> | **03-foc-pwm-eps** | 02 + 電動パワーステアリング機構 ← 本モデル |
> | 04-foc-pwm-sensorless | 02 + センサーレス制御 (誘起電圧オブザーバ + PLL) |
> | 05-foc-pwm-eps-sensorless | 03 + 04 の統合 |

---

## 概要 (Overview)

本モデルは **2 つの実行ファイル** を生成します。

| 実行ファイル | 役割 |
|--------------|------|
| `BrushlessDCMotor` | `02` と同じ BLDC モータ単体シミュレーション |
| `EpsGearboxSim` | EPS 機構を含む統合シミュレーション (本モデルの主役) |

`EpsGearboxSim` の特徴:

- **EPS 機構**: ステアリングコラム慣性・トーションバー (ばね-ダンパ)・
  減速ギア・ラック質量を含む機械系モデル
- **アシスト制御**: トーションバーの捻れから操舵トルクを検出し、
  V カーブのアシストマップで q 軸電流指令を生成
- **トルクセンサ LPF**: 機械共振の励起を防ぐためのセンサ信号フィルタ
- ドライバ操舵トルクをランプ入力として与え、ラック推力までの応答を確認

理論的背景は **[`../docs/theory/`](../docs/theory/)** を参照してください。

---

## ディレクトリ構成 (Repository Layout)

```
03-foc-pwm-eps/
├── CMakeLists.txt          # ビルド定義 (2 実行ファイルを生成)
├── README.md               # 本ファイル
├── LICENSE                 # MIT ライセンス
├── build.ps1               # Windows 用ビルドスクリプト
├── run.ps1                 # Windows 用実行スクリプト
├── src/                    # C++ ソース
│   ├── main.cpp                # BrushlessDCMotor のエントリポイント
│   ├── eps_main.cpp            # EpsGearboxSim のエントリポイント
│   ├── motor_controller.{hpp,cpp}  # PI 制御器・FOC コントローラ・PWM 換算
│   ├── motor_model.{hpp,cpp}       # モータ電気・機械モデル (プラント)
│   ├── motor_vector_conv.{hpp,cpp} # Clarke / Park 変換・中点変調
│   ├── eps_controller.{hpp,cpp}    # EPS アシストマップ (V カーブ)
│   ├── eps_gearbox_model.{hpp,cpp} # コラム・トーションバー・ラックの力学
│   ├── eps_sim_params.hpp          # EPS 機構の物理定数
│   ├── csv_verifier.{hpp,cpp}      # リファレンス CSV との回帰照合
│   └── sim_params.hpp              # モータ・シミュレーション設定
├── scripts/                # Python 可視化・解析スクリプト
│   ├── sim_viewer.py               # モータ波形ビューア (PyQt6 GUI)
│   ├── eps_viewer.py               # EPS 波形ビューア
│   ├── eps_vcurve_sweep.py         # アシストマップ V カーブのスイープ
│   ├── tn_sweep.py                 # T-n 特性スイープ
│   ├── compare_modulation.py       # 中点変調・非干渉制御の ON/OFF 比較
│   └── requirements.txt            # Python 依存パッケージ
├── data/                   # シミュレーション出力 CSV / リファレンス
└── docs/                   # 本モデル固有の図表 (EPS 機構図など)
```

---

## 必要環境 (Requirements)

| 項目 | 要件 |
|------|------|
| C++ コンパイラ | C++20 対応 (GCC 11+, Clang 14+, MSVC 2022) |
| CMake | 3.16 以上 |
| Eigen3 | 3.4 以上 (線形代数ライブラリ) |
| Python (任意) | 3.9 以上 — 可視化スクリプト用 |

### Eigen3 のインストール

```sh
# Ubuntu / Debian
sudo apt install libeigen3-dev

# macOS (Homebrew)
brew install eigen

# Windows (vcpkg)
vcpkg install eigen3
```

CMake が Eigen3 を見つけられない場合は、`FetchContent` による自動取得に
フォールバックします (ネットワーク接続が必要)。

---

## ビルド (Build)

```sh
# 1. 構成 (初回、または CMakeLists.txt 変更後)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release

# 2. ビルド (2 つの実行ファイルが生成される)
cmake --build build --config Release
```

ビルドが成功すると、プロジェクト直下に `BrushlessDCMotor` と
`EpsGearboxSim` (Windows では `.exe`) が生成されます。

```sh
# 特定のターゲットのみビルドする場合
cmake --build build --target EpsGearboxSim
```

Windows では `build.ps1` を実行しても同じ結果が得られます。

---

## 実行 (Run)

### BrushlessDCMotor (モータ単体)

```sh
./BrushlessDCMotor --iq_ref 85 --tload 4.3 --span 2.0
```

オプションは `02` と同一です (`--iq_ref` / `--tload` / `--vdc` /
`--span` / `--csv_out` / `--no_csv` / `--quiet` / `--midpoint` / `--decoupling`)。

### EpsGearboxSim (EPS 統合)

```sh
# 既定パラメータで実行
./EpsGearboxSim

# 操舵トルク最大値・ランプ時間・シミュレーション時間を指定
./EpsGearboxSim --tmax 6.0 --ramp 0.3 --span 2.0
```

| オプション | 既定値 | 説明 |
|------------|--------|------|
| `--tmax <Nm>` | eps_sim_params.hpp | ドライバ操舵トルクの最大値 [Nm] |
| `--ramp <s>` | eps_sim_params.hpp | 操舵トルクのランプ時間 [s] |
| `--span <s>` | eps_sim_params.hpp | シミュレーション時間 [s] |
| `--csv_out <path>` | data/eps_output.csv | CSV 出力先パス |
| `--no_csv` | — | CSV 出力を無効化 |
| `--quiet` | — | RESULT 行のみ出力 |
| `--midpoint` | ON | 中点変調 (SVPWM) を有効化 (既定 ON) |
| `--no-midpoint` | — | 中点変調を無効化 |
| `--decoupling` | ON | dq 軸非干渉制御を有効化 (既定 ON) |
| `--no-decoupling` | — | dq 軸非干渉制御を無効化 |

---

## 出力 (Output)

### コンソール出力

`RESULT` 行は常に出力されます。`EpsGearboxSim` の場合は EPS 機構の
定常量 (トーションバートルク・アシストトルク・ラック推力など) を示します。

### CSV ファイル

| ファイル | 内容 |
|----------|------|
| `data/sim_output.csv` | BrushlessDCMotor のモータ波形 |
| `data/pwm_waveform.csv` | PWM パルス列 |
| `data/eps_output.csv` | EpsGearboxSim の EPS 機構応答 |

`scripts/eps_viewer.py` で EPS 波形を可視化できます。

---

## Python スクリプト (`scripts/`)

事前に依存パッケージをインストールしてください。

```sh
pip install -r scripts/requirements.txt
```

| スクリプト | 説明 |
|------------|------|
| `sim_viewer.py` | モータ波形ビューア (PyQt6 GUI) |
| `eps_viewer.py` | EPS 機構応答の波形ビューア |
| `eps_vcurve_sweep.py` | アシストマップ (V カーブ) の特性スイープ |
| `tn_sweep.py` | T-n 等の特性スイープ |
| `compare_modulation.py` | 中点変調・非干渉制御の ON/OFF 波形比較 |

```sh
python scripts/eps_viewer.py
python scripts/compare_modulation.py --span 2.0
```

---

## 理論的背景 (Theory)

| ドキュメント | 内容 |
|--------------|------|
| [`docs/theory/motor-model.md`](../docs/theory/motor-model.md) | モータの電気・機械方程式 |
| [`docs/theory/foc.md`](../docs/theory/foc.md) | ベクトル制御 (FOC) の原理 |
| [`docs/theory/pwm-inverter.md`](../docs/theory/pwm-inverter.md) | PWM・三相インバータ・中点変調 |
| [`docs/theory/pi-tuning.md`](../docs/theory/pi-tuning.md) | PI ゲインの極配置設計 |
| [`docs/theory/eps.md`](../docs/theory/eps.md) | 電動パワーステアリングの力学モデル |
| [`docs/derivations.md`](../docs/derivations.md) | 数式の導出 |
| [`docs/glossary.md`](../docs/glossary.md) | 用語集 |

---

## ライセンス (License)

本プロジェクトは MIT ライセンスで公開されています。詳細は [`LICENSE`](LICENSE) を
参照してください。
