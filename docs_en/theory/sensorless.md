# Sensorless Control — Back-EMF Observer and PLL

This document explains the **position-sensorless control** of the `04` / `05` models. In the code, this corresponds to `sensorless_observer.{hpp,cpp}`.

---

## 1. Why Position-Sensorless?

Ordinary FOC measures the rotor angle with a sensor such as a resolver. The motivations for estimating this without a sensor are as follows.

- **Cost reduction** — The resolver and its interface circuitry (excitation, differential amplifier, ADC) can be omitted
- **Improved reliability** — Fewer mechanical moving parts, hence fewer failure modes
- **Miniaturization** — No sensor mounting space or wiring is needed
- **Redundancy** — Can be used together as backup control in case of resolver failure

---

## 2. Main Categories of Sensorless Control

| Method | Principle | Applicable range |
|------|------|--------|
| Back-EMF based | Back-calculate the angle from the back-EMF | Medium speed and above |
| High-frequency injection (HFI) | Exploit saliency | Low speed / standstill (suited to IPM) |
| I-f control | Force the current vector to rotate | Prevents step-out at startup |
| Extended Kalman Filter (EKF) | The rigorous version of state estimation | Full range (heavy computation) |

This code adopts the **back-EMF observer method**. It is highly accurate at medium speed and above, but because the back-EMF $e = K_e \omega$ is proportional to speed, estimation accuracy degrades at standstill and low speed.

---

## 3. Back-EMF Observer

### 3.1 Back-EMF Estimation in the αβ Frame

Subtracting the resistive drop and the inductance-derived term from the motor's phase terminal voltage leaves the back-EMF due to the rotor flux.

$$
e = v - R i - L \frac{di}{dt}
$$

This is computed in the αβ stationary frame (only the Clarke transform is needed, so it does not depend on the angle).

$$
e_\alpha = v_\alpha - R i_{\alpha,\text{prev}} - L \frac{i_\alpha - i_{\alpha,\text{prev}}}{dt}
$$

$$
e_\beta = v_\beta - R i_{\beta,\text{prev}} - L \frac{i_\beta - i_{\beta,\text{prev}}}{dt}
$$

**Discretization procedure:**

1. Three-phase → αβ transform: $i_{\alpha\beta} =$ `uvw_to_alphabeta`$(i_{uvw})$, $v_{\alpha\beta} =$ `uvw_to_alphabeta`$(v_{uvw})$
2. Apply the above equations on each axis to compute $e_\alpha,\thinspace  e_\beta$

### 3.2 Delay Compensation of the Discrete Derivative

The voltage $v$ is the control output from one step earlier, while the current $i$ is the measured value of the current step. Because the discrete derivative term $L(i - i_{\text{prev}})/dt$ contains a half-step delay, $i_{\text{prev}}$ is also used in the resistive-drop term to keep the timing consistent. This is an important refinement in the code.

### 3.3 Noise Removal by Low-Pass Filter

Due to the effect of the discrete derivative, the back-EMF estimate contains noise. It is smoothed with a first-order LPF.

$$
e_{\alpha,\text{filt}} \mathrel{+}= (e_\alpha - e_{\alpha,\text{filt}}) \cdot \alpha_{\text{lpf}}, \qquad \alpha_{\text{lpf}} = 1 - e^{-\omega_c dt}
$$

The cutoff in this code is $\omega_c = 2000\thinspace \mathrm{rad/s}$ (about 318 Hz). The LPF reduces noise at the cost of estimation delay (a trade-off).

### 3.4 Back-EMF Convention and Angle Recovery

This code uses the following convention.

$$
e_\alpha = \frac{\sqrt{2}}{2} K_e \omega \sin\theta, \qquad e_\beta = \frac{\sqrt{2}}{2} K_e \omega \cos\theta
$$

With this convention, the angle can be recovered as $\theta = \mathrm{atan2}(e_\alpha,\thinspace  e_\beta)$. However, directly taking ATAN2 causes the angle to jump due to noise, so the PLL of the next section is used.

---

## 4. Angle and Speed Estimation by PLL

A **PLL (phase-locked loop)** is a mechanism that "locks" its internal estimated angle $\hat{\theta}$ onto the true phase of the back-EMF. It can estimate angle and speed simultaneously.

### 4.1 Cross-Product Error

The error signal is formed as follows.

$$
\varepsilon = e_{\alpha,\text{filt}} \cos\hat{\theta} - e_{\beta,\text{filt}} \sin\hat{\theta} \approx C \sin(\theta_{\text{true}} - \hat{\theta})
$$

Because it becomes linear under the small-angle approximation, it can be stably driven to 0 by PI control.

### 4.2 Closed-Loop Operation of the PLL

$$
\varepsilon_i \mathrel{+}= \varepsilon \cdot dt \quad \text{(integral of the error)}
$$

$$
\hat{\omega} = K_{p,\text{pll}} \varepsilon + K_{i,\text{pll}} \varepsilon_i \quad \text{(speed estimate)}
$$

$$
\hat{\theta} \mathrel{+}= \hat{\omega} \cdot dt \quad \text{(angle update)}
$$

Finally, $\hat{\theta}$ is wrapped back into $[0,\thinspace  2\pi)$.

### 4.3 PLL Gains and Bandwidth

The values set in this code:

| Parameter | Value | Meaning |
|-----------|-----|------|
| $K_{p,\text{pll}}$ | 500 [rad/s/V] | Proportional gain |
| $K_{i,\text{pll}}$ | 100000 [rad/s²/V] | Integral gain |
| PLL bandwidth | $\approx \sqrt{K_{i,\text{pll}}} \approx 316\thinspace \mathrm{rad/s}$ (about 50 Hz) | |

The PLL bandwidth is set sufficiently lower than the LPF cutoff (2000 rad/s) so that it stably tracks the filtered back-EMF.

### 4.4 Compensation of the LPF Phase Lag

The LPF delays a signal at electrical angular speed $\omega_e$ by

$$
\varphi = \arctan\negthinspace \left(\frac{\omega_e}{\omega_c}\right)
$$

Because the back-EMF is delayed by this amount, the estimated angle lags the true angle by $\varphi$. `get_angle_deg()` compensates for this phase lag by adding $+\varphi$, keeping the steady-state angle error small.

---

## 5. Change in Steady-State Values Due to Sensorless Operation

In the 005 model, the dq transform uses the estimated angle $\hat{\theta}$ rather than the true electrical angle. Because of the LPF phase lag, an angle deviation of

$$
\Delta\theta \approx -\arctan\negthinspace \left(\frac{\omega_e}{\omega_c}\right)
$$

remains even in steady state. For example, at $\omega_e = 100\thinspace \mathrm{rad/s}$, $\Delta\theta \approx -2.86°$.

Due to this $\Delta\theta$, the dq axes controlled by the PI are slightly rotated from the "true dq axes," and the current is decomposed as follows.

$$
i_q^{\text{true}} = i_q^{\text{est}} \cos(\Delta\theta) - i_d^{\text{est}} \sin(\Delta\theta)
$$

$$
i_d^{\text{true}} = i_q^{\text{est}} \sin(\Delta\theta) + i_d^{\text{est}} \cos(\Delta\theta)
$$

Because the PI control makes $i_q^{\text{est}} = 85\thinspace \mathrm{A}$ and $i_d^{\text{est}} = 0$ track their references, when $\Delta\theta = 2.86°$:

$$
i_q^{\text{true}} \approx 85 \times \cos(2.86°) \approx 84.89\thinspace \mathrm{A} \quad \text{(about 0.12 ％ drop)}
$$

$$
i_d^{\text{true}} \approx 85 \times \sin(2.86°) \approx 4.24\thinspace \mathrm{A} \quad \text{(leaks, though it should be 0)}
$$

Raising the LPF cutoff $\omega_c$ reduces $\Delta\theta$, but there is a trade-off in that noise sensitivity worsens.

---

## 6. Startup Sequence

### 6.1 The Challenge of the Low-Speed / Standstill Range

Because the back-EMF observer relies on $e = K_e \omega$, estimation breaks down as $\omega \to 0$. True sensorless control on a real machine covers the low-speed / standstill range with V/f forced ramp, I-f control, HFI, initial-position estimation, and the like.

### 6.2 This Code's Approach — Seeded Startup

This code does not implement the above low-speed-specific logic; instead it takes a hybrid scheme of "supervised run-up → pure sensorless."

| Step | Content |
|----------|------|
| Step 1 | For the first 250 ms after startup (`kStartupSteps = 1000`), inject the true rotor angle into the observer: `observer.force_sync(true_elec_deg, true_omega_elec)` |
| Step 2 | After that, switch to pure sensorless control with `est_deg = observer.get_angle_deg(omega_elec)` |

### 6.3 Startup Improvement by Blended Transition

Switching hard from the seed to pure sensorless causes the dq frame to jump discontinuously by the small amount the estimated angle is off, producing a step in the torque waveform. This is resolved by linearly blending from the true value to the estimated value over `kBlendSteps` (equivalent to 50 ms in this code).

> **About the speed passed to `force_sync`**
> Because the PLL integrates the electrical angle, the speed argument of `force_sync` must be given the **electrical angular speed** (= mechanical angular speed × number of pole pairs), not the mechanical angular speed.

---

## 7. Code Structure (005 Project)

| File | Role |
|----------|------|
| `src/sensorless_observer.{cpp,hpp}` | Observer + PLL core |
| `src/motor_vector_conv.*` | Clarke transform (`uvw_to_alphabeta` added) |
| `src/main.cpp` | Startup sequence control (force_sync → switch to standalone) |
| `src/sim_params.hpp` | Defines `kObsLpfCutoff`, `kPllKp`, `kPllKi`, `kStartupSteps` |

---

## Related Documents

- [`coordinate-transform.md`](coordinate-transform.md) — Clarke transform (αβ)
- [`motor-model.md`](motor-model.md) — Voltage equations including back-EMF
- [`foc.md`](foc.md) — Principles of Field-Oriented Control (FOC)
- [`waveform-analysis.md`](waveform-analysis.md) — Measurement-based waveform-difference analysis
