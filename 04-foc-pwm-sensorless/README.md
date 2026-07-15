# 04 - FOC PWM Sensorless Model (BrushlessDCMotor)

A C++ / CMake simulation that adds **position sensorless control** to the PWM
drive model of `02`. Without using an angle sensor such as a resolver, it
estimates the rotor angle and speed with a back-EMF observer and a PLL, and
makes FOC work using only those estimates.

> **Series structure**
>
> | Model | Contents |
> |--------|------|
> | 01-foc-ideal-voltage | FOC basics (ideal voltage source drive) |
> | 02-foc-pwm-drive | 01 + PWM inverter drive |
> | 03-foc-pwm-eps | 02 + Electric Power Steering mechanism |
> | **04-foc-pwm-sensorless** | 02 + sensorless control ← this model |
> | 05-foc-pwm-eps-sensorless | integration of 03 + 04 |

---

## Overview

- **Target**: dq-axis current control of a surface-mounted three-phase
  synchronous motor (SPMSM)
- **Sensorless control**: Estimates the rotor angle without using an angle
  sensor.
  - **Back-EMF observer**: Estimates the back-EMF
    $e = v - R \cdot i - L \cdot di/dt$ in the stationary αβ frame and smooths
    it with a first-order LPF
  - **PLL (phase-locked loop)**: Locks the estimated angle to the phase of the
    estimated back-EMF, estimating angle and speed simultaneously
  - **LPF phase compensation**: Compensates the LPF phase lag
    $\arctan(\omega_e/\omega_c)$ to reduce the steady-state angle error
- **Startup sequence**: In the low-speed range the back-EMF is small and
  estimation breaks down, so a "seeded startup" is adopted in which the true
  angle is fed to the observer for a fixed period from startup. Afterward, it
  transitions smoothly by blending toward the estimate
- **Optional features**: Midpoint modulation and dq-axis decoupling control can
  be toggled ON/OFF via runtime flags

> **On positioning**
> The estimation algorithm of this model (back-EMF observer + PLL) is a standard
> sensorless control that works from medium speed and above. The stopped and
> low-speed ranges are covered by the startup seed; low-speed-specific logic
> equivalent to a real machine's V/f forced ramp or I-f control is not
> implemented.

For the theoretical background, see
**[`../docs_en/theory/sensorless.md`](../docs_en/theory/sensorless.md)**.

---

## Repository Layout

```
04-foc-pwm-sensorless/
├── CMakeLists.txt          # Build definition
├── README.md               # This file
├── CONTRIBUTING.md          # Contribution guide
├── LICENSE                 # MIT license
├── build.ps1               # Build script for Windows
├── run.ps1                 # Run script for Windows
├── src/                    # C++ source
│   ├── main.cpp                # Entry point / simulation loop
│   ├── motor_controller.{hpp,cpp}    # PI controller / FOC controller / PWM conversion
│   ├── motor_model.{hpp,cpp}         # Motor electrical/mechanical model (plant)
│   ├── motor_vector_conv.{hpp,cpp}   # Clarke / Park transforms / midpoint modulation
│   ├── sensorless_observer.{hpp,cpp} # Back-EMF observer + PLL
│   ├── csv_verifier.{hpp,cpp}        # Regression check against reference CSV
│   └── sim_params.hpp                # Physical constants / sensorless settings
├── scripts/                # Python visualization / analysis scripts
│   ├── sim_viewer.py               # Waveform viewer (PyQt6 GUI)
│   ├── motor_characteristics_gui.py # Motor characteristics map GUI
│   ├── tn_sweep.py                 # T-n characteristic sweep
│   ├── compare_modulation.py       # ON/OFF comparison of midpoint modulation / decoupling
│   └── requirements.txt            # Python dependencies
├── data/                   # Simulation output CSV / reference
└── docs/                   # Figures and algorithm materials specific to this model
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

---

## Run

```sh
# Run with default parameters (values in src/sim_params.hpp)
./BrushlessDCMotor

# Specify q-axis current command, load torque, DC-link voltage, and time
./BrushlessDCMotor --iq_ref 85 --tload 4.3 --vdc 48 --span 2.0

# Output the RESULT line only (machine-readable, for script integration)
./BrushlessDCMotor --quiet
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

The `RESULT` line is always emitted. For the sensorless model, the estimated
angle error `angle_err_ss` is also included.

```
RESULT omega_ss=... iq_ss=... id_ss=... tload=... te_ss=... pwm_duty=... v_rms=... angle_err_ss=...
```

### CSV files

| File | Contents |
|----------|------|
| `data/sim_output.csv` | In addition to the motor waveforms, records the estimated angle and estimation error |
| `data/pwm_waveform.csv` | PWM pulse train |

The `AngleError` column lets you check the time evolution of the error between
the true electrical angle and the estimated angle.

---

## Python scripts (`scripts/`)

Install the dependencies in advance.

```sh
pip install -r scripts/requirements.txt
```

| Script | Description |
|------------|------|
| `sim_viewer.py` | Waveform viewer (PyQt6 GUI). Can also display the estimated angle and error |
| `motor_characteristics_gui.py` | Motor characteristics map GUI |
| `tn_sweep.py` | T-n and other characteristic sweeps |
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
| [`docs_en/theory/pwm-inverter.md`](../docs_en/theory/pwm-inverter.md) | PWM / three-phase inverter / midpoint modulation |
| [`docs_en/theory/sensorless.md`](../docs_en/theory/sensorless.md) | Back-EMF observer + PLL |
| [`docs_en/theory/pi-tuning.md`](../docs_en/theory/pi-tuning.md) | Pole-placement design of PI gains |
| [`docs_en/derivations.md`](../docs_en/derivations.md) | Derivations of the equations |
| [`docs_en/glossary.md`](../docs_en/glossary.md) | Glossary |

---

## Contributing

Bug reports and improvement suggestions are welcome. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for details.

---

## License

This project is released under the MIT license. See [`LICENSE`](LICENSE) for
details.
