# bldc-foc-sim

[![CI](https://github.com/Toshiaki-Saka/bldc-foc-sim/actions/workflows/ci.yml/badge.svg)](https://github.com/Toshiaki-Saka/bldc-foc-sim/actions/workflows/ci.yml)
[![Docs](https://github.com/Toshiaki-Saka/bldc-foc-sim/actions/workflows/docs.yml/badge.svg)](https://github.com/Toshiaki-Saka/bldc-foc-sim/actions/workflows/docs.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![C++20](https://img.shields.io/badge/C%2B%2B-20-blue.svg)
![CMake](https://img.shields.io/badge/CMake-3.16%2B-064F8C.svg?logo=cmake)

English | [日本語](README.ja.md)

A C++ / CMake simulation courseware repository that uses Field-Oriented Control (FOC)
of three-phase brushless (BLDC/PMSM) motors, and its application to Electric Power
Steering (EPS), as its subject matter.

It is organized as **five models** that build up the underlying techniques one at a
time. Reading them in order gives a step-by-step understanding of FOC, PWM drive, the
EPS mechanism, and sensorless control.

---

## Model list

| Model | Content | Main additions |
|--------|------|--------------|
| [`01-foc-ideal-voltage`](01-foc-ideal-voltage/) | FOC basics (ideal voltage source drive) | dq-axis PI control, FOC loop |
| [`02-foc-pwm-drive`](02-foc-pwm-drive/) | 01 + PWM inverter drive | PWM, DC-link voltage limit |
| [`03-foc-pwm-eps`](03-foc-pwm-eps/) | 02 + Electric Power Steering mechanism | column, torsion bar, rack |
| [`04-foc-pwm-sensorless`](04-foc-pwm-sensorless/) | 02 + sensorless control | back-EMF observer + PLL |
| [`05-foc-pwm-eps-sensorless`](05-foc-pwm-eps-sensorless/) | integration of 03 + 04 | all techniques combined |

Dependencies (reading order):

```
01 ──▶ 02 ──┬─▶ 03 (EPS mechanism) ───┐
            └─▶ 04 (sensorless) ──────┴─▶ 05 (integrated)
```

The `README.md` in each model's directory describes how to build it, how to run it,
and how to interpret the output.

---

## Quick start

Every model follows the same three steps: enter the directory → build → run.
The build procedure is identical for all models.

```sh
# 1. Enter the target model's directory
cd 02-foc-pwm-drive

# 2. Build (identical for all models)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Requirements: a C++20-capable compiler, CMake 3.16 or later, and Eigen3 3.4 or later.
(On Windows, `build.ps1` / `run.ps1` in each model do the same thing.)

### Per-model run examples

Building produces an executable directly under each model directory. Models `01`,
`02`, and `04` build the motor-only `BrushlessDCMotor`; `03` and `05` additionally
build `EpsGearboxSim`, which includes the EPS mechanism (`.exe` on Windows).

| Model | Typical command | What happens |
|--------|------------------|--------------|
| `01-foc-ideal-voltage` | `./BrushlessDCMotor --iq_ref 85 --tload 4.3 --span 2.0` | Runs the FOC current loop with an ideal voltage source |
| `02-foc-pwm-drive` | `./BrushlessDCMotor --iq_ref 85 --vdc 48 --span 2.0` | PWM drive; `--midpoint` extends voltage utilization |
| `03-foc-pwm-eps` | `./EpsGearboxSim --tmax 6.0 --ramp 0.3 --span 2.0` | Applies a ramp steering torque to the EPS mechanism and evaluates the response |
| `04-foc-pwm-sensorless` | `./BrushlessDCMotor --iq_ref 85 --span 2.0` | Estimates the rotor angle sensorlessly while driving |
| `05-foc-pwm-eps-sensorless` | `./EpsGearboxSim --tmax 6.0 --ramp 0.3 --span 2.0` | Sensorless + EPS mechanism, run in an integrated fashion |

Common options: `--span <s>` (duration), `--csv_out <path>` / `--no_csv` (CSV output),
`--quiet` (emit only the RESULT line), `--midpoint` / `--decoupling` (feature on/off).
`EpsGearboxSim` additionally accepts `--tmax` (maximum steering torque) and `--ramp`
(ramp time). See each model's `README.md` for the full option details and defaults.

```sh
# Example of extracting only the RESULT line (for scripting)
./BrushlessDCMotor --quiet
```

---

## Test / CI

Each model registers a minimal CTest smoke test (a short run checking that the
`RESULT` line is emitted free of NaN/Inf).

```sh
cmake -S 02-foc-pwm-drive -B 02-foc-pwm-drive/build -DCMAKE_BUILD_TYPE=Release
cmake --build 02-foc-pwm-drive/build --config Release
ctest --test-dir 02-foc-pwm-drive/build -C Release --output-on-failure
```

GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) automatically
runs configure → build → ctest across a 5-model × Ubuntu(GCC)/Windows(MSVC) matrix.

> Because all models use the same target name `BrushlessDCMotor`, they cannot be
> combined into a single CMake tree. Each model is built and tested individually.


---

## Common features

All PWM-drive models let you toggle the following features with runtime flags
(all off by default).

| Flag | Feature |
|--------|------|
| `--midpoint` | Midpoint (min-max) modulation (SVPWM). Extends voltage utilization by a factor of $2/\sqrt{3}$ |
| `--decoupling` | dq-axis decoupling control. Cancels the inter-axis coupling with feedforward |
| `--iq_step <t> <iq>` | Steps the q-axis current command at the specified time to induce a transient |

---

## Reading the results

### Types of output

Simulation results are obtained through two paths.

| Output | Format | Content |
|------|------|------|
| `RESULT` line (standard output) | single line of key=value | Key steady-state quantities. Use `--quiet` to emit only this line, for scripting |
| `data/*.csv` | time-series CSV | Waveforms at each computation step. Split into the files in the table below |

Main keys in the `RESULT` line: `omega_ss` (steady-state speed), `iq_ss` / `id_ss`
(dq-axis currents), `te_ss` (electromagnetic torque), and `tload`. From `02` onward,
`pwm_duty` / `v_rms` are added; for sensorless (`04`/`05`), `angle_err_ss` (estimated
angle error) is added.

Which CSV files are generated depends on the model.

| File | Generating model | Content |
|----------|-----------|------|
| `data/sim_output.csv` | all models | Three-phase and dq-axis currents, torque, speed, angle (from 02 onward, also duty and phase voltages) |
| `data/pwm_waveform.csv` | 02–05 | PWM pulse train compared against the triangular carrier |
| `data/eps_output.csv` | 03 / 05 | EPS mechanism response (torsion-bar torque, assist torque, rack thrust, displacement) |
| `data/verification.csv` | all models | Reference for regression checking (referenced by the CI smoke test) |

### Python scripts for reading results (`scripts/`)

First install the dependencies (common to all models; the GUI ones use PyQt6 / matplotlib).

```sh
pip install -r 02-foc-pwm-drive/scripts/requirements.txt
```

The scripts fall into four categories by purpose. The bundled set differs slightly by model.

| Category | Script | Purpose | Reads |
|------|-----------|------|----------|
| Waveform viewer (GUI) | `sim_viewer.py` | Interactively display motor waveforms | `data/sim_output.csv` |
| Waveform viewer (GUI) | `eps_viewer.py` (03/05) | Display the EPS mechanism response | `data/eps_output.csv` |
| Characteristic sweep | `tn_sweep.py` | Sweep `iq_ref` to plot T-n / I-T / P-T / η-T characteristics | Runs the solver multiple times |
| Characteristic sweep | `motor_characteristics_gui.py` | Display motor characteristic maps (N/I/P/η vs torque) in a GUI | Runs the solver multiple times |
| Characteristic sweep | `eps_vcurve_sweep.py` (03/05) | Sweep the EPS V-curve (steering torque → assist) | Runs the solver multiple times |
| Condition comparison | `compare_modulation.py` | Compare midpoint modulation / decoupling on/off across 4 conditions | Runs the solver per condition |
| Condition comparison | `compare_decoupling_transient.py` | Compare the transient response of decoupling on/off | Runs the solver per condition |
| Static plot | `plot_result.py` (01) | Save waveforms as a PNG image | `data/sim_output.csv` |

```sh
# Example: open the waveform viewer / compare modulation conditions for 02
cd 02-foc-pwm-drive
python scripts/sim_viewer.py
python scripts/compare_modulation.py --span 2.0
```

> The viewers (`sim_viewer.py` / `eps_viewer.py`) read existing CSV files as-is.
> The sweep/comparison scripts run the solver multiple times internally and aggregate the results.

---

## Documentation

The theoretical background of motor control is collected in the repository-wide
[`docs_en/`](docs_en/) directory.

```
docs/
├── theory/
│   ├── motor-model.md          Electrical and mechanical equations of the motor
│   ├── foc.md                  Principles of Field-Oriented Control (FOC)
│   ├── coordinate-transform.md Clarke / Park transforms
│   ├── pwm-inverter.md         PWM, three-phase inverter, midpoint modulation
│   ├── pi-tuning.md            Pole-placement design of PI gains
│   ├── sensorless.md           Back-EMF observer + PLL
│   ├── eps.md                  Dynamics model of Electric Power Steering
│   └── functional-safety.md    Functional safety (HARA / ISO 26262)
├── derivations.md              Derivations of the equations
├── glossary.md                 Glossary
└── references.md               References
```

---

## License

This repository is released under the Apache License 2.0. See the root
[`LICENSE`](LICENSE) for details (an identical `LICENSE` is also bundled in each
model directory).

---

## Development note

Development of this repository was assisted by [Claude Code](https://claude.com/claude-code). Design, implementation, and verification decisions are the author's own.
