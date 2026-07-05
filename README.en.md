# bldc-foc-sim

<!-- After pushing, replace <OWNER> below with your GitHub account/org to activate the badges -->
[![CI](https://github.com/<OWNER>/bldc-foc-sim/actions/workflows/ci.yml/badge.svg)](https://github.com/<OWNER>/bldc-foc-sim/actions/workflows/ci.yml)
[![Docs](https://github.com/<OWNER>/bldc-foc-sim/actions/workflows/docs.yml/badge.svg)](https://github.com/<OWNER>/bldc-foc-sim/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![C++20](https://img.shields.io/badge/C%2B%2B-20-blue.svg)
![CMake](https://img.shields.io/badge/CMake-3.16%2B-064F8C.svg?logo=cmake)

📖 日本語: [`README.md`](README.md)

A C++ / CMake simulation courseware repository on field-oriented control (FOC) of
three-phase brushless motors (BLDC / PMSM) and its application to electric power
steering (EPS).

It is organised as **five models** that build up the underlying techniques one at a
time. Reading them in order gives a step-by-step understanding of FOC, PWM drive,
the EPS mechanism, and sensorless control.

---

## Models

| Model | Content | Main addition |
|-------|---------|---------------|
| [`01-foc-ideal-voltage`](01-foc-ideal-voltage/) | FOC basics (ideal voltage source) | dq-axis PI control, FOC loop |
| [`02-foc-pwm-drive`](02-foc-pwm-drive/) | 01 + PWM inverter drive | PWM, DC-link voltage limit |
| [`03-foc-pwm-eps`](03-foc-pwm-eps/) | 02 + electric power steering | column, torsion bar, rack |
| [`04-foc-pwm-sensorless`](04-foc-pwm-sensorless/) | 02 + sensorless control | back-EMF observer + PLL |
| [`05-foc-pwm-eps-sensorless`](05-foc-pwm-eps-sensorless/) | integration of 03 + 04 | all techniques combined |

Dependency (reading order):

```
01 ──▶ 02 ──┬─▶ 03 (EPS mechanism) ──┐
            └─▶ 04 (sensorless) ─────┴─▶ 05 (integrated)
```

Each model directory has a `README.md` describing how to build, run, and interpret
the output.

---

## Quick start

Every model follows the same three steps: enter the directory → build → run.

```sh
# 1. Enter the target model directory
cd 02-foc-pwm-drive

# 2. Build (identical for all models)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Requirements: a C++20 compiler, CMake 3.16+, and Eigen3 3.4+.
(On Windows, `build.ps1` / `run.ps1` in each model do the same thing.)

### Per-model run examples

Building produces an executable directly under each model directory. Models `01`,
`02`, `04` build the motor-only `BrushlessDCMotor`; `03` and `05` additionally build
`EpsGearboxSim`, which includes the EPS mechanism (`.exe` on Windows).

| Model | Typical command | What happens |
|-------|-----------------|--------------|
| `01-foc-ideal-voltage` | `./BrushlessDCMotor --iq_ref 85 --tload 4.3 --span 2.0` | Runs the FOC current loop with an ideal voltage source |
| `02-foc-pwm-drive` | `./BrushlessDCMotor --iq_ref 85 --vdc 48 --span 2.0` | PWM drive; `--midpoint` extends voltage utilisation |
| `03-foc-pwm-eps` | `./EpsGearboxSim --tmax 6.0 --ramp 0.3 --span 2.0` | Applies a ramp steering torque to the EPS mechanism |
| `04-foc-pwm-sensorless` | `./BrushlessDCMotor --iq_ref 85 --span 2.0` | Estimates the rotor angle sensorlessly while driving |
| `05-foc-pwm-eps-sensorless` | `./EpsGearboxSim --tmax 6.0 --ramp 0.3 --span 2.0` | Sensorless + EPS mechanism, integrated |

Common options: `--span <s>` (duration), `--csv_out <path>` / `--no_csv` (CSV output),
`--quiet` (RESULT line only), `--midpoint` / `--decoupling` (feature on/off).
`EpsGearboxSim` additionally accepts `--tmax` (max steering torque) and `--ramp`
(ramp time). See each model's `README.md` for the full option list and defaults.

---

## Test / CI

Each model registers a minimal CTest smoke test (a short run that must emit the
`RESULT` line free of NaN/Inf), plus numerical unit tests where applicable.

```sh
cmake -S 02-foc-pwm-drive -B 02-foc-pwm-drive/build -DCMAKE_BUILD_TYPE=Release
cmake --build 02-foc-pwm-drive/build --config Release
ctest --test-dir 02-foc-pwm-drive/build -C Release --output-on-failure
```

GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs
configure → build → ctest across a 5-model × Ubuntu(GCC)/Windows(MSVC) matrix.

> Because all models use the same target name `BrushlessDCMotor`, they cannot be
> combined into one CMake tree. Each model is built and tested individually.

---

## Documentation

The theoretical background lives in the shared [`docs/`](docs/) directory and is
published with MkDocs. See the Japanese `README.md` for the full page list, or build
the site locally:

```sh
pip install -r requirements-docs.txt
mkdocs serve
```

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## License

Released under the MIT License. See [`LICENSE`](LICENSE) (each model directory also
bundles an identical `LICENSE`).
