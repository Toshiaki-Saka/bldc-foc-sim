# Control Algorithm

## Overview

The simulation implements a full FOC (Field-Oriented Control) drive with a back-EMF-based sensorless observer.
One simulation step corresponds to one PWM period (250 µs at default settings).

```
┌───────────────────────────────────────────────────────────────┐
│  Seeded startup (kStartupSteps = 1000 steps = 250 ms)         │
│  observer.force_sync(true_angle, true_omega)                  │
│  est_deg = true electrical angle                              │
└───────────────────┬───────────────────────────────────────────┘
                    │ After startup
                    ▼
┌───────────────────────────────────────────────────────────────┐
│  Sensorless mode (every step)                                 │
│  observer.update(prev_voltage_uvw, current_uvw)               │
│  est_deg = observer.get_angle_deg()                           │
└───────────────────┬───────────────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────────────────────┐
│  FOC current control (MotorController::compute)               │
│  1. Clarke + Park: UVW current → dq frame                     │
│  2. PI_d: error(id* − id) → vd                                │
│  3. PI_q: error(iq* − iq) → vq                                │
│  4. Clamp |vdq| ≤ v_peak (from PWM duty limit)               │
│  5. Inverse Park: dq voltage → UVW phase voltages             │
└───────────────────┬───────────────────────────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────────────────────────┐
│  Plant model (MotorModel::update)                             │
│  1. UVW voltage → dq voltage (Park transform)                 │
│  2. Current dynamics (forward Euler)                          │
│     did/dt = (vd − R·id) / L                                  │
│     diq/dt = (vq − Ke·ω − R·iq) / L                          │
│  3. Torque: Te = Kt · iq                                      │
│  4. Angular velocity (trapezoidal): dω/dt = (Te − Tl − B·ω)/J│
│  5. Mechanical & electrical angle integration                  │
│  6. CSV logging + PWM waveform generation                     │
└───────────────────────────────────────────────────────────────┘
```

---

## Clarke / Park Transforms

Implemented in `src/motor_vector_conv.cpp` using amplitude-invariant scaling.

**Clarke (UVW → αβ)**

$$
\begin{bmatrix} \alpha \cr \beta \end{bmatrix}
= \frac{\sqrt{2}}{3}
\begin{bmatrix}
  \cos 0 & \cos \frac{2\pi}{3} & \cos \frac{-2\pi}{3} \cr
  \sin 0 & \sin \frac{2\pi}{3} & \sin \frac{-2\pi}{3}
\end{bmatrix}
\begin{bmatrix} u \cr v \cr w \end{bmatrix}
$$

**Park (αβ → dq)**

$$
\begin{bmatrix} d \cr q \end{bmatrix}
=
\begin{bmatrix}  \cos\theta & \sin\theta \cr -\sin\theta & \cos\theta \end{bmatrix}
\begin{bmatrix} \alpha \cr \beta \end{bmatrix}
$$

---

## PI Current Controller Gains (2nd-order Pole Placement)

The d/q-axis current loops are modelled as first-order plants:

$$
G(s) = \frac{1}{Ls + R}
$$

With a PI controller `C(s) = Kp + Ki/s`, the closed-loop characteristic polynomial is:

$$
s^2 + \frac{Kp}{L} s + \frac{Ki}{L} = s^2 + 2\zeta\omega_n s + \omega_n^2
$$

Matching coefficients:

$$
K_p = 2\zeta\omega_n L - R \qquad K_i = \omega_n^2 L
$$

Default: `ωn = 1000 rad/s`, `ζ = 1.0` (critically damped).  
Electrical time constant `τe = L/R = 1 ms`; sampling period `Ts = 250 µs` → `ωn·Ts = 0.25` (discretisation error acceptable).

---

## Sensorless Back-EMF Observer + PLL

Implemented in `src/sensorless_observer.cpp`.

### Step 1 — Back-EMF estimation (αβ frame)

$$
e_\alpha = v_\alpha(k-1) - R\thinspace i_\alpha(k-1) - L\thinspace \frac{i_\alpha(k) - i_\alpha(k-1)}{\Delta t}
$$

$$
e_\beta  = v_\beta(k-1)  - R\thinspace i_\beta(k-1)  - L\thinspace \frac{i_\beta(k)  - i_\beta(k-1)}{\Delta t}
$$

> `v(k-1)` is used because the applied voltage at the previous step drove the current change observed at step `k`.

### Step 2 — First-order LPF

$$
e_{\alpha,\text{filt}}(k) = e_{\alpha,\text{filt}}(k-1) + \alpha_{\text{lpf}} \bigl(e_\alpha(k) - e_{\alpha,\text{filt}}(k-1)\bigr)
$$

$$
\alpha_{\text{lpf}} = 1 - e^{-\omega_c \Delta t}, \quad \omega_c = 2000 \text{ rad/s}
$$

### Step 3 — PLL angle tracking

Back-EMF convention (from amplitude-invariant Clarke + SPMSM model):

$$
e_\alpha = \frac{\sqrt{2}}{2} K_e \omega \sin\theta, \quad e_\beta = \frac{\sqrt{2}}{2} K_e \omega \cos\theta
$$

Cross-product error (linearises to $C\sin(\theta_{true} - \theta_{est}) \approx C(\theta_{true} - \theta_{est})$ near lock):

$$
\varepsilon = e_{\alpha,\text{filt}} \cos\hat{\theta} - e_{\beta,\text{filt}} \sin\hat{\theta}
$$

PLL update:

$$
\hat{\omega}(k) = K_p \varepsilon + K_i \int \varepsilon \thinspace  dt
$$

$$
\hat{\theta}(k) = \hat{\theta}(k-1) + \hat{\omega}(k) \Delta t
$$

### Seeded startup

For the first `kStartupSteps` (250 ms), `force_sync(true_angle, true_omega)` is called after each `update()`.
This warms up the LPF and PLL integral before switching to blind sensorless mode — equivalent to the open-loop V/f ramp used in real drives.

---

## PWM Waveform Generation

Centre-aligned (symmetrical, triangle-carrier) modulation.  
Carrier period: `kPwmCarrierPeriod = 25 µs` (40 kHz).

Per simulation step (`Δt = 250 µs = 10 carrier cycles`):

```
duty_u = 0.5 + Vu / Vdc
duty_v = 0.5 + Vv / Vdc
duty_w = 0.5 + Vw / Vdc

for each sub-sample k:
    φ  = fmod(t / T_carrier, 1.0)
    tri = φ < 0.5 ? 2φ : 2(1−φ)      // triangle carrier [0, 1]
    PwmU = (duty_u > tri) ? Vdc : 0
```

Output is written to `data/pwm_waveform.csv` with columns `Time_s, PwmU_V, PwmV_V, PwmW_V`.
