# Parameter Reference

All parameters are defined in `src/sim_params.hpp`.
Change values there and rebuild to retune the simulation.

---

## Simulation time

| Constant | Value | Unit | Description |
|----------|-------|------|-------------|
| `kResolution` | 0.00025 | s | Simulation step size (= PWM period, 250 µs) |
| `kCalcSpan` | 5.0 | s | Default simulation duration |

---

## Motor model parameters

Based on **[1]** Pang, Jang, Lee — *ICCAS 2005*, Table 1 and **[2]** ATO 110WDM06020-48V datasheet.

| Constant | Value | Unit | Description |
|----------|-------|------|-------------|
| `kKt` | 0.0533 | Nm/A | Torque constant |
| `kKe` | 0.0533 | V·s/rad | Back-EMF constant |
| `kR` | 0.1 | Ω | Phase resistance |
| `kL` | 0.0001 | H | Phase inductance |
| `kB` | 1e-2 / (2π) | Nm·s/rad | Viscous damping coefficient |
| `kJ` | 3.5e-4 | kg·m² | Rotor inertia |

Steady-state operating point (default):

$$
T_e = K_t \cdot i_q^* = 0.0533 \times 85 \approx 4.53\ \text{Nm}
$$

$$
\omega_{ss} = \frac{T_e - T_{load}}{B} = \frac{4.53 - 4.3}{10^{-2}/2\pi} \approx 144\ \text{rad/s} \approx 1380\ \text{rpm}
$$

---

## Current controller tuning

| Constant | Value | Unit | Description |
|----------|-------|------|-------------|
| `kWn` | 1000 | rad/s | Natural frequency for pole placement |
| `kZeta` | 1.0 | — | Damping ratio (1.0 = critically damped) |

Derived gains (computed in `main.cpp`):

$$
K_p = 2\zeta\omega_n L - R = 2 \times 1.0 \times 1000 \times 0.0001 - 0.1 = 0.1\ \text{V/A}
$$

$$
K_i = \omega_n^2 L = 1000^2 \times 0.0001 = 100\ \text{V/(A·s)}
$$

---

## Default simulation conditions

| Constant | Value | Unit | Description |
|----------|-------|------|-------------|
| `kDefaultIqRef` | 85.0 | A | Default q-axis current reference (≈4.5 Nm) |
| `kDefaultTload` | 4.3 | Nm | Default load torque |

---

## PWM output parameters

| Constant | Value | Unit | Description |
|----------|-------|------|-------------|
| `kVdc` | 48.0 | V | DC link voltage |
| `kPwmMaxDuty` | 0.95 | — | Maximum duty cycle (at `kPwmMaxAmp`) |
| `kPwmMaxAmp` | 125.0 | A | q-axis current at maximum duty cycle |
| `kPwmCarrierPeriod` | 0.000025 | s | Triangle carrier period (40 kHz) |

Duty-to-current mapping (linear, clamped):

$$
\text{duty} = \operatorname{clamp}\!\left(\frac{|i_q^*|}{k_{\text{PwmMaxAmp}}},\ 0,\ 1\right) \times k_{\text{PwmMaxDuty}}
= \operatorname{clamp}\!\left(\frac{85}{125},\ 0,\ 1\right) \times 0.95 = 0.646\ (64.6\%)
$$

---

## Sensorless observer parameters

| Constant | Value | Unit | Description |
|----------|-------|------|-------------|
| `kObsLpfCutoff` | 2000 | rad/s | Back-EMF LPF cutoff frequency |
| `kPllKp` | 500 | rad/s / V | PLL proportional gain |
| `kPllKi` | 100000 | rad/s² / V | PLL integral gain |
| `kStartupSteps` | 1000 | steps | Seeded startup duration (= 250 ms) |

PLL natural frequency (approximate, at steady-state back-EMF amplitude $C$):

$$
C = \frac{\sqrt{2}}{2} K_e \omega_{ss} \approx 0.707 \times 0.0533 \times 144 \approx 5.4\ \text{V}
$$

$$
\omega_{n,pll} = \sqrt{C \cdot K_i} \approx \sqrt{5.4 \times 100000} \approx 735\ \text{rad/s}
$$

$$
\zeta_{pll} = \frac{C \cdot K_p}{2\,\omega_{n,pll}} \approx \frac{5.4 \times 500}{2 \times 735} \approx 1.84 \quad \text{(over-damped)}
$$

LPF cutoff (2000 rad/s) is >10× the electrical frequency (≈144 rad/s at steady state),
giving good noise rejection while preserving back-EMF phase information.

---

## References

- **[1]** Pang, Jang, Lee, "Steering Wheel Torque Control of Electric Power Steering by PD-Control," *ICCAS 2005*, Table 1.
- **[2]** ATO 110WDM06020-48V 1kW BLDC Motor datasheet.
