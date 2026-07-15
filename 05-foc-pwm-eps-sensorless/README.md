# 05 - FOC PWM EPS Sensorless Integrated Model

The top-level model of this series, integrating the EPS mechanism of `03` and
the sensorless control of `04`. It combines a BLDC motor driven by position
sensorless control with an Electric Power Steering mechanism to reproduce the
behavior of an entire EPS system that uses no resolver.

> **Series structure**
>
> | Model | Contents |
> |--------|------|
> | 01-foc-ideal-voltage | FOC basics (ideal voltage source drive) |
> | 02-foc-pwm-drive | 01 + PWM inverter drive |
> | 03-foc-pwm-eps | 02 + Electric Power Steering mechanism |
> | 04-foc-pwm-sensorless | 02 + sensorless control (back-EMF observer + PLL) |
> | **05-foc-pwm-eps-sensorless** | integration of 03 + 04 ← this model |

---

## Overview

This model generates **two executables**.

| Executable | Role |
|--------------|------|
| `BrushlessDCMotor` | The same standalone sensorless BLDC motor simulation as `04` |
| `EpsGearboxSim` | Integrated simulation of sensorless control + EPS mechanism |

Integrated elements:

- **Sensorless control** (from `04`): Rotor angle and speed estimation via a
  back-EMF observer + PLL. Includes LPF phase compensation, seeded startup, and
  blend transition
- **EPS mechanism** (from `03`): Dynamics model of the steering column, torsion
  bar, reduction gear, and rack, together with a V-curve assist map
- **Optional features**: Midpoint modulation and dq-axis decoupling control can
  be toggled ON/OFF via runtime flags

It is a configuration that makes the EPS assist behavior work without using a
resolver, bringing all the elemental technologies of this series together into
one.

For the theoretical background, see **[`../docs_en/theory/`](../docs_en/theory/)**.

---

## Repository Layout

```
05-foc-pwm-eps-sensorless/
├── CMakeLists.txt          # Build definition (generates 2 executables)
├── README.md               # This file
├── LICENSE                 # MIT license
├── build.ps1               # Build script for Windows
├── run.ps1                 # Run script for Windows
├── src/                    # C++ source
│   ├── main.cpp                # Entry point for BrushlessDCMotor
│   ├── eps_main.cpp            # Entry point for EpsGearboxSim
│   ├── motor_controller.{hpp,cpp}    # PI controller / FOC controller / PWM conversion
│   ├── motor_model.{hpp,cpp}         # Motor electrical/mechanical model (plant)
│   ├── motor_vector_conv.{hpp,cpp}   # Clarke / Park transforms / midpoint modulation
│   ├── sensorless_observer.{hpp,cpp} # Back-EMF observer + PLL
│   ├── eps_controller.{hpp,cpp}      # EPS assist map (V-curve)
│   ├── eps_gearbox_model.{hpp,cpp}   # Dynamics of column / torsion bar / rack
│   ├── eps_sim_params.hpp            # Physical constants of the EPS mechanism
│   ├── csv_verifier.{hpp,cpp}        # Regression check against reference CSV
│   └── sim_params.hpp                # Motor / sensorless settings
├── scripts/                # Python visualization / analysis scripts
│   ├── sim_viewer.py               # Motor waveform viewer (PyQt6 GUI)
│   ├── eps_viewer.py               # EPS waveform viewer
│   ├── eps_vcurve_sweep.py         # Sweep of the assist-map V-curve
│   ├── tn_sweep.py                 # T-n characteristic sweep
│   ├── compare_modulation.py       # ON/OFF comparison of midpoint modulation / decoupling
│   └── requirements.txt            # Python dependencies
├── data/                   # Simulation output CSV / reference
└── docs/                   # Figures specific to this model
```

---

## Requirements

| Item | Requirement |
|------|------|
| C++ compiler | C++20 support (GCC 11+, Clang 14+, MSVC 2022) |
| CMake | 3.16 or later |
| Eigen3 | 3.4 or later (linear algebra library) |
| Python (optional) | 3.9 or later — for visualization scripts |

### Installing Eigen3

```sh
# Ubuntu / Debian
sudo apt install libeigen3-dev

# macOS (Homebrew)
brew install eigen

# Windows (vcpkg)
vcpkg install eigen3
```

If CMake cannot find Eigen3, it falls back to automatic retrieval via
`FetchContent` (a network connection is required).

---

## Build

```sh
# 1. Configure (first time, or after changing CMakeLists.txt)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release

# 2. Build (two executables are generated)
cmake --build build --config Release
```

Once the build succeeds, `BrushlessDCMotor` and `EpsGearboxSim` (`.exe` on
Windows) are generated directly under the project.

```sh
# To build only a specific target
cmake --build build --target EpsGearboxSim
```

On Windows, running `build.ps1` produces the same result.

---

## Run

### BrushlessDCMotor (sensorless motor standalone)

```sh
./BrushlessDCMotor --iq_ref 85 --tload 4.3 --span 2.0
```

The options are identical to `04` (`--iq_ref` / `--tload` / `--vdc` /
`--span` / `--csv_out` / `--no_csv` / `--quiet` / `--midpoint` / `--decoupling`).

### EpsGearboxSim (sensorless + EPS integrated)

```sh
# Run with default parameters
./EpsGearboxSim

# Specify the steering torque maximum, ramp time, and simulation time
./EpsGearboxSim --tmax 6.0 --ramp 0.3 --span 2.0
```

| Option | Default | Description |
|------------|--------|------|
| `--tmax <Nm>` | eps_sim_params.hpp | Maximum driver steering torque [Nm] |
| `--ramp <s>` | eps_sim_params.hpp | Ramp time of the steering torque [s] |
| `--span <s>` | eps_sim_params.hpp | Simulation time [s] |
| `--csv_out <path>` | data/eps_output.csv | CSV output path |
| `--no_csv` | — | Disable CSV output |
| `--quiet` | — | Output the RESULT line only |
| `--midpoint` | ON | Enable midpoint modulation (SVPWM) (default ON) |
| `--no-midpoint` | — | Disable midpoint modulation |
| `--decoupling` | ON | Enable dq-axis decoupling control (default ON) |
| `--no-decoupling` | — | Disable dq-axis decoupling control |

---

## Output

### Console output

The `RESULT` line is always emitted. For `BrushlessDCMotor` it includes the
estimated angle error `angle_err_ss`, and for `EpsGearboxSim` it includes the
steady-state quantities of the EPS mechanism.

### CSV files

| File | Contents |
|----------|------|
| `data/sim_output.csv` | Motor waveforms / estimated angle / estimation error |
| `data/pwm_waveform.csv` | PWM pulse train |
| `data/eps_output.csv` | EPS mechanism response of EpsGearboxSim |

Visualization is available with `scripts/sim_viewer.py` /
`scripts/eps_viewer.py`.

---

## Python scripts (`scripts/`)

Install the dependencies in advance.

```sh
pip install -r scripts/requirements.txt
```

| Script | Description |
|------------|------|
| `sim_viewer.py` | Motor waveform viewer (PyQt6 GUI). Also displays the estimated angle and error |
| `eps_viewer.py` | Waveform viewer for the EPS mechanism response |
| `eps_vcurve_sweep.py` | Characteristic sweep of the assist map (V-curve) |
| `tn_sweep.py` | T-n and other characteristic sweeps |
| `compare_modulation.py` | Waveform comparison of midpoint modulation / decoupling ON/OFF |

```sh
python scripts/eps_viewer.py
python scripts/compare_modulation.py --span 2.0
```

---

## Theory

| Document | Contents |
|--------------|------|
| [`docs_en/theory/motor-model.md`](../docs_en/theory/motor-model.md) | Electrical and mechanical equations of the motor |
| [`docs_en/theory/foc.md`](../docs_en/theory/foc.md) | Principle of Field-Oriented Control (FOC) |
| [`docs_en/theory/pwm-inverter.md`](../docs_en/theory/pwm-inverter.md) | PWM / three-phase inverter / midpoint modulation |
| [`docs_en/theory/sensorless.md`](../docs_en/theory/sensorless.md) | Back-EMF observer + PLL |
| [`docs_en/theory/eps.md`](../docs_en/theory/eps.md) | Dynamics model of Electric Power Steering |
| [`docs_en/theory/pi-tuning.md`](../docs_en/theory/pi-tuning.md) | Pole-placement design of PI gains |
| [`docs_en/derivations.md`](../docs_en/derivations.md) | Derivations of the equations |
| [`docs_en/glossary.md`](../docs_en/glossary.md) | Glossary |

---

## License

This project is released under the MIT license. See [`LICENSE`](LICENSE) for
details.
