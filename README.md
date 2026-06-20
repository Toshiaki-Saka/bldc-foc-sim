# bldc-foc-sim

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

各モデルのディレクトリにある `README.md` に、ビルド方法・実行方法・
出力の説明が記載されています。

---

## クイックスタート

```sh
# 任意のモデルのディレクトリへ移動
cd 02-foc-pwm-drive

# ビルド
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

# 実行
./BrushlessDCMotor --span 2.0
```

必要環境: C++20 対応コンパイラ、CMake 3.16 以上、Eigen3 3.4 以上。
詳細は各モデルの `README.md` を参照してください。

---

## 共通機能

すべての PWM 駆動モデルは、以下の機能を実行時フラグで切り替えられます
(いずれも既定 OFF)。

| フラグ | 機能 |
|--------|------|
| `--midpoint` | 中点変調 (SVPWM)。電圧利用率を 2/√3 倍に拡張 |
| `--decoupling` | dq 軸非干渉制御。軸間結合をフィードフォワードで打ち消す |
| `--iq_step <t> <iq>` | 指定時刻に q 軸電流指令をステップさせ、過渡を発生させる |

`scripts/` 以下の Python ツールで、これらの効果を波形比較できます。

| スクリプト | 用途 |
|------------|------|
| `compare_modulation.py` | 中点変調・非干渉制御の ON/OFF を 4 条件で比較 |
| `compare_decoupling_transient.py` | 非干渉制御の過渡応答を ON/OFF で比較 |
| `sim_viewer.py` | シミュレーション結果 CSV の波形ビューア (GUI) |

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

本リポジトリは MIT ライセンスで公開されています。各モデルディレクトリの
`LICENSE` ファイルを参照してください。
