# 01 - FOC 理想電圧源モデル (BrushlessDCMotor)

三相ブラシレスモータ (BLDC / PMSM) のベクトル制御 (FOC) を最小構成で再現する
C++ / CMake シミュレーションです。インバータの電圧飽和や PWM を含まない
「理想電圧源」モデルで、FOC の電流制御ループそのものの挙動を学ぶための
出発点となるモデルです。

> **シリーズ構成**
> 本リポジトリは 5 つのモデルで構成され、要素を段階的に積み上げていきます。
> 本モデル `01` はその最初のステップです。
>
> | モデル | 内容 |
> |--------|------|
> | **01-foc-ideal-voltage** | FOC 基本 (理想電圧源駆動) ← 本モデル |
> | 02-foc-pwm-drive | 01 + PWM インバータ駆動 |
> | 03-foc-pwm-eps | 02 + 電動パワーステアリング機構 |
> | 04-foc-pwm-sensorless | 02 + センサーレス制御 (誘起電圧オブザーバ + PLL) |
> | 05-foc-pwm-eps-sensorless | 03 + 04 の統合 |

---

## 概要 (Overview)

- **対象**: 表面磁石型 三相同期モータ (SPMSM, $L_d = L_q$) の dq 軸電流制御
- **制御**: dq 軸それぞれに PI 制御器を持つ FOC。ゲインは極配置法で自動算出
- **駆動**: 理想電圧源。PI 制御器が要求した電圧をそのままモータへ印加
  (PWM・DC リンク電圧制限・キャリアは扱わない → `02` 以降で導入)
- **オプション機能**: 中点変調・dq 軸非干渉制御を実行時フラグで ON/OFF 可能
  (理想電圧源では電圧制限が無いため効果は限定的。学習・比較用)

理論的背景は **[`../docs/theory/`](../docs/theory/)** を参照してください。

---

## ディレクトリ構成 (Repository Layout)

```
01-foc-ideal-voltage/
├── CMakeLists.txt          # ビルド定義
├── README.md               # 本ファイル
├── LICENSE                 # MIT ライセンス
├── build.ps1               # Windows 用ビルドスクリプト
├── run.ps1                 # Windows 用実行スクリプト
├── src/                    # C++ ソース
│   ├── main.cpp                # エントリポイント・シミュレーションループ
│   ├── motor_controller.{hpp,cpp}  # PI 制御器・FOC コントローラ
│   ├── motor_model.{hpp,cpp}       # モータ電気・機械モデル (プラント)
│   ├── motor_vector_conv.{hpp,cpp} # Clarke / Park 変換・中点変調
│   ├── csv_verifier.{hpp,cpp}      # リファレンス CSV との回帰照合
│   └── sim_params.hpp              # 物理定数・シミュレーション設定
├── scripts/                # Python 可視化・解析スクリプト
│   ├── sim_viewer.py               # 波形ビューア (PyQt6 GUI)
│   ├── motor_characteristics_gui.py # モータ特性マップ GUI
│   ├── tn_sweep.py                 # T-n / I-T / P-T / η-T 特性スイープ
│   ├── plot_result.py              # 波形 PNG 出力
│   ├── compare_modulation.py       # 中点変調・非干渉制御の ON/OFF 比較
│   └── requirements.txt            # Python 依存パッケージ
├── data/                   # シミュレーション出力 CSV / リファレンス
└── docs/                   # 本モデル固有の図表
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

```powershell
./build.ps1
```

---

## 実行 (Run)

```sh
# 既定パラメータで実行 (src/sim_params.hpp の値)
./BrushlessDCMotor

# q 軸電流指令・負荷トルク・シミュレーション時間を指定
./BrushlessDCMotor --iq_ref 85 --tload 4.3 --span 2.0

# RESULT 行のみ出力 (機械可読、スクリプト連携用)
./BrushlessDCMotor --quiet
```

### コマンドラインオプション

| オプション | 既定値 | 説明 |
|------------|--------|------|
| `--iq_ref <A>` | sim_params.hpp | q 軸電流指令値 [A] |
| `--tload <Nm>` | sim_params.hpp | 負荷トルク [Nm] |
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

`RESULT` 行は常に出力され、定常状態の主要量を機械可読な形式で示します。

```
RESULT omega_ss=... iq_ss=... id_ss=... tload=... te_ss=...
```

`--quiet` を付けない場合、これに加えて T-n 特性表や CSV 照合結果が表示されます。

### CSV ファイル (`data/sim_output.csv`)

各計算ステップごとに、三相電流・dq 軸電流・電磁トルク・回転速度・角度などを
記録します。`scripts/sim_viewer.py` で波形として可視化できます。

---

## Python スクリプト (`scripts/`)

事前に依存パッケージをインストールしてください。

```sh
pip install -r scripts/requirements.txt
```

| スクリプト | 説明 |
|------------|------|
| `sim_viewer.py` | `data/sim_output.csv` の波形ビューア (PyQt6 GUI) |
| `motor_characteristics_gui.py` | モータ特性マップ (N/I/P/η vs トルク) GUI |
| `tn_sweep.py` | `iq_ref` を変えて複数回実行し T-n 等の特性をプロット |
| `plot_result.py` | 波形を PNG 画像として保存 |
| `compare_modulation.py` | 中点変調・非干渉制御の ON/OFF 波形比較 |

```sh
python scripts/sim_viewer.py
python scripts/compare_modulation.py --span 2.0
```

---

## 理論的背景 (Theory)

モータモデル・FOC・座標変換・PI チューニングの理論は、リポジトリ共通の
ドキュメントにまとめてあります。

| ドキュメント | 内容 |
|--------------|------|
| [`docs/theory/motor-model.md`](../docs/theory/motor-model.md) | モータの電気・機械方程式 |
| [`docs/theory/foc.md`](../docs/theory/foc.md) | ベクトル制御 (FOC) の原理 |
| [`docs/theory/coordinate-transform.md`](../docs/theory/coordinate-transform.md) | Clarke / Park 変換 |
| [`docs/theory/pi-tuning.md`](../docs/theory/pi-tuning.md) | PI ゲインの極配置設計 |
| [`docs/derivations.md`](../docs/derivations.md) | 数式の導出 |
| [`docs/glossary.md`](../docs/glossary.md) | 用語集 |

---

## ライセンス (License)

本プロジェクトは MIT ライセンスで公開されています。詳細は [`LICENSE`](LICENSE) を
参照してください。
