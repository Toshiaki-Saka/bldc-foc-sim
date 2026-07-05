# 04 - FOC PWM センサーレスモデル (BrushlessDCMotor)

`02` の PWM 駆動モデルに **位置センサーレス制御** を追加した C++ / CMake
シミュレーションです。レゾルバ等の角度センサを使わず、誘起電圧オブザーバと
PLL によってロータ角度・速度を推定し、その推定値だけで FOC を成立させます。

> **シリーズ構成**
>
> | モデル | 内容 |
> |--------|------|
> | 01-foc-ideal-voltage | FOC 基本 (理想電圧源駆動) |
> | 02-foc-pwm-drive | 01 + PWM インバータ駆動 |
> | 03-foc-pwm-eps | 02 + 電動パワーステアリング機構 |
> | **04-foc-pwm-sensorless** | 02 + センサーレス制御 ← 本モデル |
> | 05-foc-pwm-eps-sensorless | 03 + 04 の統合 |

---

## 概要 (Overview)

- **対象**: 表面磁石型 三相同期モータ (SPMSM) の dq 軸電流制御
- **センサーレス制御**: 角度センサを使わずにロータ角度を推定する。
  - **誘起電圧オブザーバ**: αβ 固定座標系で誘起電圧 $e = v - R \cdot i - L \cdot di/dt$
    を推定し、1 次 LPF で平滑化
  - **PLL (位相同期ループ)**: 推定誘起電圧の位相に推定角をロックさせ、
    角度・速度を同時に推定
  - **LPF 位相補償**: LPF の位相遅れ $\arctan(\omega_e/\omega_c)$ を補償し、定常角度誤差を低減
- **起動シーケンス**: 低速域では誘起電圧が小さく推定が破綻するため、
  起動から一定期間は真の角度をオブザーバに与える「シードあり起動」を採用。
  その後、推定値へ滑らかにブレンド遷移する
- **オプション機能**: 中点変調・dq 軸非干渉制御を実行時フラグで ON/OFF 可能

> **位置付けについて**
> 本モデルの推定アルゴリズム (誘起電圧オブザーバ + PLL) は中速以上で機能する
> 標準的なセンサーレス制御です。停止・低速域は起動シードでカバーしており、
> 実機の V/f 強制ランプや I-f 制御に相当する低速専用ロジックは実装していません。

理論的背景は **[`../docs/theory/sensorless.md`](../docs/theory/sensorless.md)** を
参照してください。

---

## ディレクトリ構成 (Repository Layout)

```
04-foc-pwm-sensorless/
├── CMakeLists.txt          # ビルド定義
├── README.md               # 本ファイル
├── CONTRIBUTING.md          # コントリビューションガイド
├── LICENSE                 # MIT ライセンス
├── build.ps1               # Windows 用ビルドスクリプト
├── run.ps1                 # Windows 用実行スクリプト
├── src/                    # C++ ソース
│   ├── main.cpp                # エントリポイント・シミュレーションループ
│   ├── motor_controller.{hpp,cpp}    # PI 制御器・FOC コントローラ・PWM 換算
│   ├── motor_model.{hpp,cpp}         # モータ電気・機械モデル (プラント)
│   ├── motor_vector_conv.{hpp,cpp}   # Clarke / Park 変換・中点変調
│   ├── sensorless_observer.{hpp,cpp} # 誘起電圧オブザーバ + PLL
│   ├── csv_verifier.{hpp,cpp}        # リファレンス CSV との回帰照合
│   └── sim_params.hpp                # 物理定数・センサーレス設定
├── scripts/                # Python 可視化・解析スクリプト
│   ├── sim_viewer.py               # 波形ビューア (PyQt6 GUI)
│   ├── motor_characteristics_gui.py # モータ特性マップ GUI
│   ├── tn_sweep.py                 # T-n 特性スイープ
│   ├── compare_modulation.py       # 中点変調・非干渉制御の ON/OFF 比較
│   └── requirements.txt            # Python 依存パッケージ
├── data/                   # シミュレーション出力 CSV / リファレンス
└── docs/                   # 本モデル固有の図表・アルゴリズム資料
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

# 2. ビルド
cmake --build build --config Release
```

ビルドが成功すると、プロジェクト直下に実行ファイル `BrushlessDCMotor`
(Windows では `BrushlessDCMotor.exe`) が生成されます。

Windows では `build.ps1` を実行しても同じ結果が得られます。

---

## 実行 (Run)

```sh
# 既定パラメータで実行 (src/sim_params.hpp の値)
./BrushlessDCMotor

# q 軸電流指令・負荷トルク・DC リンク電圧・時間を指定
./BrushlessDCMotor --iq_ref 85 --tload 4.3 --vdc 48 --span 2.0

# RESULT 行のみ出力 (機械可読、スクリプト連携用)
./BrushlessDCMotor --quiet
```

### コマンドラインオプション

| オプション | 既定値 | 説明 |
|------------|--------|------|
| `--iq_ref <A>` | sim_params.hpp | q 軸電流指令値 [A] |
| `--tload <Nm>` | sim_params.hpp | 負荷トルク [Nm] |
| `--vdc <V>` | sim_params.hpp | DC リンク電圧 [V] |
| `--span <s>` | sim_params.hpp | シミュレーション時間 [s] |
| `--csv_out <path>` | data/sim_output.csv | CSV 出力先パス |
| `--no_csv` | — | CSV 出力を無効化 |
| `--quiet` | — | RESULT 行のみ出力 (詳細出力を抑制) |
| `--midpoint` | ON | 中点変調 (SVPWM) を有効化 (既定 ON) |
| `--no-midpoint` | — | 中点変調を無効化 |
| `--decoupling` | ON | dq 軸非干渉制御を有効化 (既定 ON) |
| `--no-decoupling` | — | dq 軸非干渉制御を無効化 |

---

## 出力 (Output)

### コンソール出力

`RESULT` 行は常に出力されます。センサーレスモデルでは推定角度誤差
`angle_err_ss` も含まれます。

```
RESULT omega_ss=... iq_ss=... id_ss=... tload=... te_ss=... pwm_duty=... v_rms=... angle_err_ss=...
```

### CSV ファイル

| ファイル | 内容 |
|----------|------|
| `data/sim_output.csv` | モータ波形に加え、推定角度・推定誤差を記録 |
| `data/pwm_waveform.csv` | PWM パルス列 |

`AngleError` 列で、真の電気角と推定角の誤差の時間変化を確認できます。

---

## Python スクリプト (`scripts/`)

事前に依存パッケージをインストールしてください。

```sh
pip install -r scripts/requirements.txt
```

| スクリプト | 説明 |
|------------|------|
| `sim_viewer.py` | 波形ビューア (PyQt6 GUI)。推定角度・誤差も表示可能 |
| `motor_characteristics_gui.py` | モータ特性マップ GUI |
| `tn_sweep.py` | T-n 等の特性スイープ |
| `compare_modulation.py` | 中点変調・非干渉制御の ON/OFF 波形比較 |

```sh
python scripts/sim_viewer.py
python scripts/compare_modulation.py --span 2.0
```

---

## 理論的背景 (Theory)

| ドキュメント | 内容 |
|--------------|------|
| [`docs/theory/motor-model.md`](../docs/theory/motor-model.md) | モータの電気・機械方程式 |
| [`docs/theory/foc.md`](../docs/theory/foc.md) | ベクトル制御 (FOC) の原理 |
| [`docs/theory/pwm-inverter.md`](../docs/theory/pwm-inverter.md) | PWM・三相インバータ・中点変調 |
| [`docs/theory/sensorless.md`](../docs/theory/sensorless.md) | 誘起電圧オブザーバ + PLL |
| [`docs/theory/pi-tuning.md`](../docs/theory/pi-tuning.md) | PI ゲインの極配置設計 |
| [`docs/derivations.md`](../docs/derivations.md) | 数式の導出 |
| [`docs/glossary.md`](../docs/glossary.md) | 用語集 |

---

## コントリビューション (Contributing)

バグ報告・改善提案を歓迎します。詳細は [`CONTRIBUTING.md`](CONTRIBUTING.md) を
参照してください。

---

## ライセンス (License)

本プロジェクトは MIT ライセンスで公開されています。詳細は [`LICENSE`](LICENSE) を
参照してください。
