# 02 - FOC PWM Drive Model (BrushlessDCMotor)

A C++ / CMake simulation that adds **PWM inverter drive** to the ideal voltage
source model of `01`. By accounting for the DC-link voltage (Vdc), the
triangular carrier, and the duty-cycle upper limit, it becomes a model one step
closer to the drive circuit of a real ECU.

> **Series structure**
>
> | Model | Contents |
> |--------|------|
> | 01-foc-ideal-voltage | FOC basics (ideal voltage source drive) |
> | **02-foc-pwm-drive** | 01 + PWM inverter drive ← this model |
> | 03-foc-pwm-eps | 02 + Electric Power Steering mechanism |
> | 04-foc-pwm-sensorless | 02 + sensorless control (back-EMF observer + PLL) |
> | 05-foc-pwm-eps-sensorless | integration of 03 + 04 |

---

## Overview

- **Target**: dq-axis current control of a surface-mounted three-phase
  synchronous motor (SPMSM, $L_d = L_q$)
- **Control**: FOC with a PI controller on each of the d- and q-axes. Gains are
  computed automatically by pole placement
- **Drive**: **PWM inverter drive**. The differences from `01` are as follows.
  - Accounts for the DC-link voltage `Vdc` and sets an upper limit on the phase
    voltage that can be applied
  - Converts the q-axis current command into a PWM duty cycle
  - Compares against a triangular carrier (40 kHz) to generate a pulse train,
    output to a separate CSV
  - In the high-speed range, the back-EMF $K_e \omega$ eats up the voltage
    limit and the rotational speed reaches a ceiling
- **Optional features**: Midpoint modulation and dq-axis decoupling control can
  be toggled ON/OFF via runtime flags
  - Enabling midpoint modulation extends the voltage utilization by a factor of
    $2/\sqrt{3}$, raising the ceiling rotational speed

For the theoretical background, see **[`../docs_en/theory/`](../docs_en/theory/)**.

---

## Repository Layout

```
02-foc-pwm-drive/
├── CMakeLists.txt          # Build definition
├── README.md               # This file
├── LICENSE                 # MIT license
├── build.ps1               # Build script for Windows
├── run.ps1                 # Run script for Windows
├── src/                    # C++ source
│   ├── main.cpp                # Entry point / simulation loop
│   ├── motor_controller.{hpp,cpp}  # PI controller / FOC controller / PWM conversion
│   ├── motor_model.{hpp,cpp}       # Motor electrical/mechanical model (plant)
│   ├── motor_vector_conv.{hpp,cpp} # Clarke / Park transforms / midpoint modulation
│   ├── csv_verifier.{hpp,cpp}      # Regression check against reference CSV
│   └── sim_params.hpp              # Physical constants / simulation settings
├── scripts/                # Python visualization / analysis scripts
│   ├── sim_viewer.py               # Waveform viewer (PyQt6 GUI)
│   ├── motor_characteristics_gui.py # Motor characteristics map GUI
│   ├── tn_sweep.py                 # T-n / I-T / P-T / η-T characteristic sweep
│   ├── compare_modulation.py       # ON/OFF comparison of midpoint modulation / decoupling
│   └── requirements.txt            # Python dependencies
└── data/                   # Simulation output CSV / reference
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

# Specify q-axis current command, load torque, DC-link voltage, and time
./BrushlessDCMotor --iq_ref 85 --tload 4.3 --vdc 48 --span 2.0

# Output the RESULT line only (machine-readable, for script integration)
./BrushlessDCMotor --quiet

# Run with midpoint modulation enabled (improves voltage utilization)
./BrushlessDCMotor --midpoint
```

### Command-line options

| Option | Default | Description |
|------------|--------|------|
| `--iq_ref <A>` | sim_params.hpp | q-axis current command [A] |
| `--tload <Nm>` | sim_params.hpp | Load torque [Nm] |
| `--vdc <V>` | sim_params.hpp | DC-link voltage [V] |
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
RESULT omega_ss=... iq_ss=... id_ss=... tload=... te_ss=... pwm_duty=... v_rms=...
```

When `--quiet` is not given, the T-n characteristic table and CSV verification
results are shown in addition to this.

### CSV files

| File | Contents |
|----------|------|
| `data/sim_output.csv` | Three-phase currents, dq-axis currents, torque, rotational speed, angle, duty, phase voltages |
| `data/pwm_waveform.csv` | PWM pulse train compared against the triangular carrier |

The data can be visualized as waveforms with `scripts/sim_viewer.py`.

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
| `compare_modulation.py` | Waveform comparison of midpoint modulation / decoupling ON/OFF |

```sh
python scripts/sim_viewer.py
python scripts/compare_modulation.py --span 2.0
```

---

## Theory

| Document | Contents |
|--------------|------|
| [`docs_en/theory/motor-model.md`](../docs_en/theory/motor-model.md) | Electrical and mechanical equations of the motor |
| [`docs_en/theory/foc.md`](../docs_en/theory/foc.md) | Principle of Field-Oriented Control (FOC) |
| [`docs_en/theory/coordinate-transform.md`](../docs_en/theory/coordinate-transform.md) | Clarke / Park transforms |
| [`docs_en/theory/pwm-inverter.md`](../docs_en/theory/pwm-inverter.md) | PWM / three-phase inverter / midpoint modulation |
| [`docs_en/theory/pi-tuning.md`](../docs_en/theory/pi-tuning.md) | Pole-placement design of PI gains |
| [`docs_en/derivations.md`](../docs_en/derivations.md) | Derivations of the equations |
| [`docs_en/glossary.md`](../docs_en/glossary.md) | Glossary |

---

## License

This project is released under the MIT license. See [`LICENSE`](LICENSE) for
details.
