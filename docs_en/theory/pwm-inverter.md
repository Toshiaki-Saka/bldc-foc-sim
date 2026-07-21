# PWM, the Three-Phase Inverter, and Midpoint Modulation

This document explains the **PWM inverter drive** and **midpoint modulation** handled by the `02` and later models. In the code, this corresponds to the PWM conversion section of `motor_controller.cpp` and the midpoint modulation function in `motor_vector_conv.cpp`.

---

## 1. The Three-Phase Inverter and PWM

In a real machine, the DC link voltage $`V_{dc}`$ is switched by a three-phase bridge circuit (6 switching devices) to produce an arbitrary three-phase voltage. The scheme in which each phase's switch is turned ON/OFF at high speed, and the equivalent voltage is controlled by its **duty cycle** (the fraction of ON time), is **PWM (pulse-width modulation)**.

![Three-phase bridge circuit (Y-connection)](images/three_phase_bridge_circuit.png)

*A three-phase bridge circuit made of 6 FETs (IGBTs). Each phase has an upper arm and a lower arm. On the right are the Y-connected three-phase coils.*

A triangular carrier is compared against the voltage command to generate a pulse train. The carrier frequency in this code is **40 kHz** (period 25 µs).

### PWM Duty and Dead Time

In three-phase sinusoidal drive, all upper- and lower-arm FETs start driving from a balanced state at 50 % PWM duty.

- To pass + side current into any phase → output at 50–95 % duty
- To pass − side current → output at 5–50 % duty

The 5 % margin is for the **dead time**. Turning ON the upper and lower arm FETs of the same phase simultaneously would cause a short circuit, so a brief period during which both are OFF is inserted.

---

## 2. Difference Between the A-Type and B-Type Models

| Model | Drive scheme | Upper bound on applied voltage | Purpose |
|--------|----------|----------------|------|
| `01`/`02` ideal voltage source (A-type) | Apply the PI output directly | None (unlimited) | Pure understanding of the FOC loop |
| `03` and later, PWM (B-type) | Convert the PI output into a duty cycle | Yes (limited by $`V_{dc}`$) | Educational material closer to a real ECU |

The A-type and B-type agree completely in $`i_q`$, $`T_e`$, and $`\omega`$ from startup until $`t \approx 0.59\thinspace \mathrm{s}`$. A difference appears only after $`\omega`$ has risen sufficiently.

---

## 3. Speed Ceiling Caused by Back-EMF

In steady state, the q-axis voltage balance is as follows.

$$
v_q = R i_q + K_e \omega_m
$$

As the motor rotates, the back-EMF $`K_e \omega_m`$ grows, and once it reaches the upper limit of the applicable voltage, no more $`i_q`$ can be driven. As a result, the rotational speed hits a ceiling. This is a realistic behavior specific to the PWM drive model.

Because the A-type is an ideal voltage source with no upper limit, $`\omega`$ continues to rise further. Measured ($`t = 5\thinspace \mathrm{s}`$): $`\omega`$ goes from 144.8 → 132.1 rad/s (about 9 % drop), and $`i_q`$ from 85.0 → 84.6 A.

---

## 4. Midpoint Modulation (Zero-Sequence Injection / SVPWM)

In ordinary sinusoidal PWM, $`V_{dc}/2`$ is the limit of the phase-voltage peak, but by **shifting the neutral-point potential of the three phases**, the phase-voltage peak can be lowered without changing the line-to-line voltage. This allows a larger fundamental amplitude for the same $`V_{dc}`$.

This code adopts the **min-max method** (equivalent to space-vector modulation, SVPWM).

$$
v_{zero} = -\frac{\max(v_U, v_V, v_W) + \min(v_U, v_V, v_W)}{2}
$$

$$
v_U' = v_U + v_{zero}, \quad v_V' = v_V + v_{zero}, \quad v_W' = v_W + v_{zero}
$$

### Effect

- The line-to-line voltage does not change → **the motor torque is unchanged**
- The phase-voltage peak is lowered → for the same $`V_{dc}`$, the fundamental amplitude can be extended by a factor of $`\dfrac{2}{\sqrt{3}} \approx 1.155`$ (about 15.5%)
- As a result, the rotational speed and current that were capped by voltage saturation improve

Measured example (`02` model, $`i_q^{\ast} = 85\thinspace \mathrm{A}`$):

| Condition | $`v_{rms}`$ | $`\omega`$ steady-state value | $`i_q`$ steady-state value |
|------|-----------|-----------------|--------------|
| Midpoint modulation OFF | 10.96 V | 132.1 rad/s | 84.62 A |
| Midpoint modulation ON | 12.66 V (+15.5%) | 144.8 rad/s (+9.6%) | 85.00 A (reaches command) |

---

## 5. Diagnosing the Current Drop (85 A → 84 A)

### Symptom

When run with `--iq_ref 85`, the steady-state current stays at about **84.62 A** and does not reach the commanded value of 85 A.

### Root Cause: PWM Voltage Saturation

The PWM duty conversion in `motor_controller.cpp` computes $`v_{\text{peak}}`$ from the q-axis current command in a fixed manner.

$$
\text{duty} = \text{clamp}\negthinspace \left(\frac{|i_q^{\ast}|}{k_{\text{PwmMaxAmp}}},\thinspace  0,\thinspace  1\right) \times k_{\text{PwmMaxDuty}}
$$

$$
v_{\text{peak}} = \text{duty} \times \frac{V_{dc}}{2}
$$

Substituting the default parameters ($`i_q^{\ast} = 85\thinspace \mathrm{A}`$, $`k_{\text{PwmMaxAmp}} = 125\thinspace \mathrm{A}`$, $`k_{\text{PwmMaxDuty}} = 0.95`$, $`V_{dc} = 48\thinspace \mathrm{V}`$):

$$
v_{\text{peak}} = \frac{85}{125} \times 0.95 \times \frac{48}{2} = 15.504\thinspace \mathrm{V}
$$

On the other hand, driving 85 A in steady state requires a q-axis voltage that includes the back-EMF.

$$
v_{q,\text{required}} = R i_q + K_e \omega_{ss} = 0.1 \times 85 + 0.0533 \times 144.8 \approx 8.50 + 7.72 = 16.22\thinspace \mathrm{V}
$$

Because $`v_{q,\text{required}} (16.22\thinspace \mathrm{V}) > v_{\text{peak}} (15.504\thinspace \mathrm{V})`$, the PI output is clamped and the current does not reach the commanded value.

### Confirming the Steady-State Settling Point

Since the condition for a steady state to hold after clamping is $`v_q = v_{\text{peak}}`$:

$$
R i_{q,ss} + K_e \omega_{ss} = 15.504\thinspace \mathrm{V}
$$

Verifying with the CSV data ($`i_{q,ss} \approx 84.62\thinspace \mathrm{A}`$, $`\omega_{ss} \approx 132.1\thinspace \mathrm{rad/s}`$):

$$
0.1 \times 84.62 + 0.0533 \times 132.1 = 8.46 + 7.04 = 15.50\thinspace \mathrm{V} \checkmark
$$

This matches $`v_{\text{peak}}`$ exactly, confirming that voltage clamping is the cause.

### Solutions

| Method | Command example | Effect |
|------|-----------|------|
| Enable midpoint modulation | `./BrushlessDCMotor --midpoint` | $`v_{\text{peak}}`$ becomes $`2/\sqrt{3}`$ times larger → 17.91 V. Amply covers 16.22 V |
| Raise the DC voltage | `./BrushlessDCMotor --vdc 55` | $`v_{\text{peak}}`$ increases in proportion to the rise in $`V_{dc}`$ |
| Raise `kPwmMaxDuty` | Edit `sim_params.hpp` | Relaxes the duty-cycle upper limit (on a real machine, consult the thermal design) |

---

## 6. PWM Duty Conversion

In `motor_controller.cpp`, the PWM duty cycle is linearly converted from the q-axis current command.

$$
v_{\text{peak}} = \text{clamp}\negthinspace \left(\frac{|i_q^{\ast}|}{k_{\text{PwmMaxAmp}}},\thinspace  0,\thinspace  1\right) \times k_{\text{PwmMaxDuty}} \times \frac{V_{dc}}{2} \times \begin{cases} \frac{2}{\sqrt{3}} & \text{(midpoint modulation ON)} \cr 1 & \text{(midpoint modulation OFF)} \end{cases}
$$

`kPwmMaxAmp` is the current corresponding to the maximum duty, and `kPwmMaxDuty` is the upper limit of the duty cycle (95 %).

---

## 7. Implementation Switch (Midpoint Modulation)

Midpoint modulation can be toggled by a runtime flag (default OFF).

```sh
./BrushlessDCMotor --midpoint
```

You can compare the ON/OFF waveforms with `scripts/compare_modulation.py`.

In the code, `MotorVectorConv::apply_midpoint_modulation()` performs the zero-sequence injection, and `MotorController::compute()` applies it according to the flag. When midpoint modulation is ON, the PWM duty conversion also reflects the extension of the voltage utilization ($`2/\sqrt{3}`$ times).

---

## Related Documents

- [`foc.md`](foc.md) — Principles of Field-Oriented Control (FOC)
- [`coordinate-transform.md`](coordinate-transform.md) — Clarke / Park transforms
- [`motor-model.md`](motor-model.md) — Electrical and mechanical equations of the motor
- [`waveform-analysis.md`](waveform-analysis.md) — Measurement-based waveform-difference analysis
