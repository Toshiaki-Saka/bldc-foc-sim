# PI Gain Design by Pole Placement

This document explains how the gains of the dq-axis PI controllers in `bldc-foc-sim` are chosen. In the code, this corresponds to the design parameters in `sim_params.hpp` and the gain-calculation formulas in `main.cpp`.

---

## 1. Design Philosophy

In this code, the PI gains $K_p$ and $K_i$ are not tuned directly. Instead, the designer chooses only two parameters that characterize the closed-loop response.

| Parameter | Symbol | Meaning |
|------------|------|------|
| Natural angular frequency | `kWn` ($\omega_n$) | Speed of the response |
| Damping ratio | `kZeta` ($\zeta$) | Amount of overshoot |

From these two, `main.cpp` automatically computes $K_p$ and $K_i$. The design philosophy is: "Specify the response characteristics, and the equations determine the gains."

---

## 2. Structure of the Control Loop

The electrical plant (the voltage-to-current transfer function) is a first-order lag system.

$$
G(s) = \frac{1}{Ls + R}
$$

A PI controller is combined with it.

$$
C(s) = K_p + \frac{K_i}{s} = \frac{K_p s + K_i}{s}
$$

The closed-loop transfer function becomes:

$$
T(s) = \frac{C(s) G(s)}{1 + C(s) G(s)}
$$

Organizing the denominator gives:

$$
\text{denominator} = s^2 + \frac{R + K_p}{L} s + \frac{K_i}{L}
$$

---

## 3. Matching the Standard Second-Order System

The standard form of a second-order system is:

$$
s^2 + 2\zeta\omega_n s + \omega_n^2
$$

Match the closed-loop denominator to this standard form (pole placement).

$$
\frac{R + K_p}{L} = 2\zeta\omega_n \quad \Rightarrow \quad K_p = 2\zeta\omega_n L - R
$$

$$
\frac{K_i}{L} = \omega_n^2 \quad \Rightarrow \quad K_i = \omega_n^2 L
$$

These are the gain-calculation formulas used in this code. They are implemented in `main.cpp` as follows:

```cpp
const double kKp = 2.0 * kZeta * kWn * kL - kR;
const double kKi = kWn * kWn * kL;
```

---

## 4. How to Choose the Parameters

### Step 1 — Choose kWn (natural angular frequency)

`kWn` determines the response speed of the current loop. A rule of thumb is **several times the reciprocal of the electrical time constant**.

- Electrical time constant $\tau_e = L/R$. In this code $L = 0.1\,\mathrm{mH}$ and $R = 0.1\,\Omega$, so $\tau_e = 1\,\mathrm{ms}$, and its reciprocal is $1000\,\mathrm{rad/s}$
- Set `kWn` to roughly 1 to 10 times this value. This code adopts `kWn = 1000 rad/s`
- **Upper-bound constraint**: For a sampling period $T_s = 250\,\mu\mathrm{s}$, a rule of thumb is $\omega_n T_s < 0.3$. Here $1000 \times 0.00025 = 0.25$, which is within the acceptable range. Exceeding this makes the discretization error large and can lead to divergence

### Step 2 — Choose kZeta (damping ratio)

`kZeta` determines the amount of overshoot in the closed-loop response.

| kZeta | Behavior |
|-------|------|
| 1.0 | Critically damped. No overshoot, fastest settling (adopted by the 002 model) |
| 0.7–0.8 | Slight overshoot. Close to the response of a real machine (adopted by the 003/004 models) |
| < 0.7 | Large overshoot. Oscillation remains during settling |
| > 1.0 | Overdamped. The response becomes sluggish |

For applications that emphasize smoothness, such as EPS, set it closer to 1.0; to emphasize responsiveness, set it closer to 0.7.

---

## 5. Physical Meaning of the Computed Gains

- **$K_p = 2\zeta\omega_n L - R$** : Proportional gain. It cancels the plant pole $-R/L$ and acts to speed up the response
- **$K_i = \omega_n^2 L$** : Integral gain. It acts to drive the steady-state error to zero

When $\zeta = 1$ and $\omega_n = 1000\,\mathrm{rad/s}$:

$$
K_p = 2 \times 1 \times 1000 \times 0.0001 - 0.1 = 0.1
$$

$$
K_i = 1000^2 \times 0.0001 = 100
$$

These are used in the `PidController` in `motor_controller.cpp` as $K_p e_p + K_i e_i$ (`e_p` is the proportional error, and `e_i` is the trapezoidally integrated error).

---

## 6. Verification — Judging Correctness from the Waveforms

- **Rise time** $\approx \dfrac{5}{\zeta \omega_n}$. For $\zeta=1,\, \omega_n=1000$, settling takes about 5 ms
- **Overshoot ratio** $= \exp\!\left(-\dfrac{\pi\zeta}{\sqrt{1-\zeta^2}}\right)$. For $\zeta=0.8$, about 1.5 %
- Check the rise and settling from the waveforms of the `iq` and `omega` columns in `data/motor_log.csv`
- Use `csv_verifier` to compare against the reference CSV and detect deviations from the expected values

---

## 7. Cases Where Tuning Fails

| Symptom | Cause | Remedy |
|------|------|------|
| $K_p$ becomes negative | The region where $2\zeta\omega_n L < R$ | Increase `kWn` |
| iq diverges or oscillates | `kWn` is too high ($\omega_n T_s > 0.3$) | Decrease `kWn` |
| Settling is too slow | `kWn` is low, or in the B-type PWM voltage saturation is the rate-limiting factor | Increase `kWn`. If saturation is the cause, review the $V_{dc}$ side |
| Steady-state error remains | The integral is not taking effect | Check $K_i$ and the accumulation of the integral error |

---

## Related Documents

- [`foc.md`](foc.md) — Principles of Field-Oriented Control (FOC)
- [`motor-model.md`](motor-model.md) — Electrical and mechanical equations of the motor
