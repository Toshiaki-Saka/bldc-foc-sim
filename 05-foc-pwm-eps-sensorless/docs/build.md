# ビルド手順 / Build Instructions

## 必要環境

- CMake 3.15 以上
- C++20 対応コンパイラ (MSVC / GCC 11+ / Clang 14+)
- [Eigen3](https://eigen.tuxfamily.org/) 3.4.0 以上

---

## Configure (初回 / CMakeLists.txt 変更後)

```bash
cmake -S . -B build
```

Eigen3 のパスが自動検出されない場合:

```bash
cmake -S . -B build -DEigen3_DIR=<path/to/eigen>/cmake
```

---

## Build

**Release ビルド (推奨):**

```bash
cmake --build build --config Release
```

**Debug ビルド:**

```bash
cmake --build build --config Debug
```

**特定ターゲットのみ:**

```bash
# BrushlessDCMotor のみ
cmake --build build --config Release --target BrushlessDCMotor

# EPS シミュレータのみ
cmake --build build --config Release --target EpsGearboxSim
```

---

## 出力ファイル

ビルド成功後、プロジェクトルートに実行ファイルが生成されます:

```
BrushlessDCMotor.exe   (Windows) / BrushlessDCMotor   (Linux/macOS)
EpsGearboxSim.exe      (Windows) / EpsGearboxSim       (Linux/macOS)
```

---

## 実行

```bash
./BrushlessDCMotor.exe
./EpsGearboxSim.exe
```

実行後、`data/` ディレクトリに CSV ファイルが出力されます。  
Python スクリプトで結果を可視化できます:

```bash
python scripts/sim_viewer.py   # BrushlessDCMotor の結果
python scripts/eps_viewer.py   # EPS シミュレータの結果
```

---

## 再ビルド (2回目以降)

Configure 不要で、以下だけで再ビルドできます:

```bash
cmake --build build --config Release
```
