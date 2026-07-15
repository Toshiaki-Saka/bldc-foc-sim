# bldc-foc-sim Theory

Theory material on Field-Oriented Control (FOC) of three-phase brushless (BLDC/PMSM) motors and on Electric Power Steering (EPS).

---

## Theory document index

| Document | Contents |
|-------------|------|
| [Motor model](theory/motor-model.md) | dq-axis voltage equations, mechanical equations, discretization |
| [Coordinate transform](theory/coordinate-transform.md) | Mathematics of the Clarke and Park transforms |
| [Field-Oriented Control (FOC)](theory/foc.md) | PI control, decoupling, comparison of Type A / Type B models |
| [PI gain design](theory/pi-tuning.md) | Gain computation by pole placement |
| [PWM inverter](theory/pwm-inverter.md) | Three-phase bridge, midpoint modulation, voltage saturation analysis |
| [Sensorless control](theory/sensorless.md) | Back-EMF observer, PLL, startup sequence |
| [Electric Power Steering](theory/eps.md) | EPS mechanism, assist map, control block diagram |
| [Waveform difference analysis](theory/waveform-analysis.md) | Type A vs Type B, measured analysis of sensorless startup |
| [Functional safety](theory/functional-safety.md) | Comprehensive HARA of major automotive systems, ASIL, ISO 26262 safety requirement derivation flow |

---

## How to read the documents

```
motor-model.md          ← Understand the fundamental motor equations
      │
coordinate-transform.md ← Understand the coordinate transforms (Clarke/Park)
      │
foc.md                  ← Grasp the overall picture of Field-Oriented Control
      │
pi-tuning.md            ← Learn how to design the PI gains
      │
pwm-inverter.md         ← Understand the practical constraints of PWM drive
      │
sensorless.md           ← Learn position-sensorless control
      │
eps.md                  ← Understand the application to EPS
      │
functional-safety.md    ← Understand functional safety (HARA / ISO 26262)
```

---

## Viewing locally

```sh
pip install -r requirements-docs.txt
mkdocs serve
```

Open `http://localhost:8000` in a browser and the equations render correctly.
