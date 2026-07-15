# 01 - FOC Ideal Voltage Source Model (BrushlessDCMotor)

A C++ / CMake simulation that reproduces Field-Oriented Control (FOC) of a
three-phase brushless (BLDC/PMSM) motor in a minimal configuration. It uses an
"ideal voltage source" model that includes neither inverter voltage saturation
nor PWM, serving as the starting point for studying the behavior of the FOC
current control loop itself.

> **Series structure**
> This repository consists of five models that build up the elements step by step.
> This model `01` is the first step.
>
> | Model | Contents |
> |--------|------|
> | **01-foc-ideal-voltage** | FOC basics (ideal voltage source drive) ← this model |
> | 02-foc-pwm-drive | 01 + PWM inverter drive |
> | 03-foc-pwm-eps | 02 + Electric Power Steering mechanism |
> | 04-foc-pwm-sensorless | 02 + sensorless control (back-EMF observer + PLL) |
> | 05-foc-pwm-eps-sensorless | integration of 03 + 04 |

---

## Overview

- **Target**: dq-axis current control of a surface-mounted three-phase
  synchronous motor (SPMSM, $L_d = L_q$)
- **Control**: FOC with a PI controller on each of the d- and q-axes. Gains are
  computed automatically by pole placement
- **Drive**: Ideal voltage source. The voltage requested by the PI controllers
  is applied to the motor as-is (PWM, DC-link voltage limits, and the carrier
  are not handled → introduced from `02` onward)
- **Optional features**: Midpoint modulation and dq-axis decoupling control can
  be toggled ON/OFF via runtime flags (with an ideal voltage source there is no
  voltage limit, so the effect is limited; for study and comparison)

For the theoretical background, see **[`../docs_en/theory/`](../docs_en/theory/)**.

---

## Repository Layout

```
01-foc-ideal-voltage/
├── CMakeLists.txt          # Build definition
├── README.md               # This file
├── LICENSE                 # MIT license
├── build.ps1               # Build script for Windows
├── run.ps1                 # Run script for Windows
├── src/                    # C++ source
│   ├── main.cpp                # Entry point / simulation loop
│   ├── motor_controller.{hpp,cpp}  # PI controller / FOC controller
│   ├── motor_model.{hpp,cpp}       # Motor electrical/mechanical model (plant)
│   ├── motor_vector_conv.{hpp,cpp} # Clarke / Park transforms / midpoint modulation
│   ├── csv_verifier.{hpp,cpp}      # Regression check against reference CSV
│   └── sim_params.hpp              # Physical constants / simulation settings
├── scripts/                # Python visualization / analysis scripts
│   ├── sim_viewer.py               # Waveform viewer (PyQt6 GUI)
│   ├── motor_characteristics_gui.py # Motor characteristics map GUI
│   ├── tn_sweep.py                 # T-n / I-T / P-T / η-T characteristic sweep
│   ├── plot_result.py              # Waveform PNG output
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

# 2. Build
cmake --build build --config Release
```

Once the build succeeds, the executable `BrushlessDCMotor`
(`BrushlessDCMotor.exe` on Windows) is generated directly under the project.

On Windows, running `build.ps1` produces the same result.

```powershell
./build.ps1
```

---

## Run

```sh
# Run with default parameters (values in src/sim_params.hpp)
./BrushlessDCMotor

# Specify q-axis current command, load torque, and simulation time
./BrushlessDCMotor --iq_ref 85 --tload 4.3 --span 2.0

# Output the RESULT line only (machine-readable, for script integration)
./BrushlessDCMotor --quiet
```

### Command-line options

| Option | Default | Description |
|------------|--------|------|
| `--iq_ref <A>` | sim_params.hpp | q-axis current command [A] |
| `--tload <Nm>` | sim_params.hpp | Load torque [Nm] |
| `--span <s>` | sim_params.hpp | Simulation time [s] |
| `--csv_out <path>` | data/sim_output.csv | CSV output path |
| `--no_csv` | — | Disable CSV output |
| `--quiet` | — | Output the RESULT line only (suppress detailed output) |
| `--midpoint` | ON | Enable midpoint modulation (SVPWM) (default ON) |
| `--no-midpoint` | — | Disable midpoint modulation |
| `--decoupling` | ON | Enable dq-axis decoupling control (default ON) |
| `--no-decoupling` | — | Disable dq-axis decoupling control |

---

## Output

### Console output

The `RESULT` line is always emitted and reports the key steady-state quantities
in a machine-readable form.

```
RESULT omega_ss=... iq_ss=... id_ss=... tload=... te_ss=...
```

When `--quiet` is not given, the T-n characteristic table and CSV verification
results are shown in addition to this.

### CSV file (`data/sim_output.csv`)

For each computation step, it records the three-phase currents, dq-axis
currents, electromagnetic torque, rotational speed, angle, and so on. The data
can be visualized as waveforms with `scripts/sim_viewer.py`.

---

## Python scripts (`scripts/`)

Install the dependencies in advance.

```sh
pip install -r scripts/requirements.txt
```

| Script | Description |
|------------|------|
| `sim_viewer.py` | Waveform viewer for `data/sim_output.csv` (PyQt6 GUI) |
| `motor_characteristics_gui.py` | Motor characteristics map (N/I/P/η vs torque) GUI |
| `tn_sweep.py` | Runs multiple times while varying `iq_ref` and plots T-n and other characteristics |
| `plot_result.py` | Saves waveforms as PNG images |
| `compare_modulation.py` | Waveform comparison of midpoint modulation / decoupling ON/OFF |

```sh
python scripts/sim_viewer.py
python scripts/compare_modulation.py --span 2.0
```

---

## Theory

The theory of the motor model, FOC, coordinate transforms, and PI tuning is
collected in the repository-wide documentation.

| Document | Contents |
|--------------|------|
| [`docs_en/theory/motor-model.md`](../docs_en/theory/motor-model.md) | Electrical and mechanical equations of the motor |
| [`docs_en/theory/foc.md`](../docs_en/theory/foc.md) | Principle of Field-Oriented Control (FOC) |
| [`docs_en/theory/coordinate-transform.md`](../docs_en/theory/coordinate-transform.md) | Clarke / Park transforms |
| [`docs_en/theory/pi-tuning.md`](../docs_en/theory/pi-tuning.md) | Pole-placement design of PI gains |
| [`docs_en/derivations.md`](../docs_en/derivations.md) | Derivations of the equations |
| [`docs_en/glossary.md`](../docs_en/glossary.md) | Glossary |

---

## License

This project is released under the MIT license. See [`LICENSE`](LICENSE) for
details.
