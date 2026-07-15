# Build Instructions

## Requirements

- CMake 3.15 or later
- A C++20-capable compiler (MSVC / GCC 11+ / Clang 14+)
- [Eigen3](https://eigen.tuxfamily.org/) 3.4.0 or later

---

## Configure (first time / after changing CMakeLists.txt)

```bash
cmake -S . -B build
```

If the Eigen3 path is not detected automatically:

```bash
cmake -S . -B build -DEigen3_DIR=<path/to/eigen>/cmake
```

---

## Build

**Release build (recommended):**

```bash
cmake --build build --config Release
```

**Debug build:**

```bash
cmake --build build --config Debug
```

**A specific target only:**

```bash
# BrushlessDCMotor only
cmake --build build --config Release --target BrushlessDCMotor

# EPS simulator only
cmake --build build --config Release --target EpsGearboxSim
```

---

## Output files

After a successful build, the executables are generated at the project root:

```
BrushlessDCMotor.exe   (Windows) / BrushlessDCMotor   (Linux/macOS)
EpsGearboxSim.exe      (Windows) / EpsGearboxSim       (Linux/macOS)
```

---

## Run

```bash
./BrushlessDCMotor.exe
./EpsGearboxSim.exe
```

After running, CSV files are written to the `data/` directory.
You can visualize the results with the Python scripts:

```bash
python scripts/sim_viewer.py   # BrushlessDCMotor results
python scripts/eps_viewer.py   # EPS simulator results
```

---

## Rebuild (subsequent builds)

No configure step is needed; you can rebuild with just:

```bash
cmake --build build --config Release
```
