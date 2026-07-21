# Derivation of the equations

This document summarizes the derivations of the main equations used in
`bldc-foc-sim`. It is supplementary material referenced from each theory document.

---

## 1. Derivation of the Clarke transform (three-phase → αβ)

The three-phase windings are arranged 120° apart in space. The magnetomotive
force vectors produced by the U, V, and W phases are projected onto the two
mutually orthogonal axes α and β.

Aligning the U phase with the α axis, the unit vectors of each phase axis are

$$
\hat{e}_U = (1,\ 0), \quad \hat{e}_V = \negthinspace \left(-\tfrac{1}{2},\ \tfrac{\sqrt{3}}{2}\right), \quad \hat{e}_W = \negthinspace \left(-\tfrac{1}{2},\ -\tfrac{\sqrt{3}}{2}\right)
$$

The α and β components are the sum of each phase quantity projected onto these axis directions.

$$
\alpha = U \cdot 1 + V \cdot \left(-\tfrac{1}{2}\right) + W \cdot \left(-\tfrac{1}{2}\right)
$$

$$
\beta  = U \cdot 0 + V \cdot \tfrac{\sqrt{3}}{2} + W \cdot \left(-\tfrac{\sqrt{3}}{2}\right)
$$

Multiplying by the scale factor $`\tfrac{2}{3}`$ that makes it amplitude-invariant yields the Clarke transform.

$$
\alpha = \frac{2}{3}\negthinspace \left(U - \frac{V}{2} - \frac{W}{2}\right), \qquad \beta  = \frac{2}{3}\negthinspace \left(\frac{\sqrt{3}}{2}V - \frac{\sqrt{3}}{2}W\right)
$$

Under the three-phase balance condition $`U + V + W = 0`$, the amplitude of the
three-phase sinusoids matches the amplitude of the αβ quantities.

---

## 2. Derivation of the Park transform (αβ → dq)

αβ is a stationary frame, while dq is a frame that rotates synchronously with
the rotor at angle $`\theta`$. A component viewed from the rotating frame equals
the stationary-frame quantity rotated by $`-\theta`$. From the rotation matrix,

$$
d =  \alpha\cos\theta + \beta\sin\theta, \qquad q = -\alpha\sin\theta + \beta\cos\theta
$$

For the inverse transform, simply rotate by $`\theta`$ (transpose of the rotation matrix = its inverse).

$$
\alpha = d\cos\theta - q\sin\theta, \qquad \beta  = d\sin\theta + q\cos\theta
$$

---

## 3. Pole placement of the PI gains (detailed derivation)

The electrical plant (voltage → current) is a first-order lag system.

$$
G(s) = \frac{1}{Ls + R}
$$

The PI controller is

$$
C(s) = K_p + \frac{K_i}{s} = \frac{K_p s + K_i}{s}
$$

The open-loop transfer function is

$$
C(s)\thinspace G(s) = \frac{K_p s + K_i}{s\thinspace (Ls + R)}
$$

The denominator polynomial of the closed-loop transfer function $`T(s) = CG/(1 + CG)`$ is

$$
s(Ls + R) + (K_p s + K_i) = Ls^2 + (R + K_p)s + K_i
$$

Divide both sides by $`L`$ to normalize.

$$
s^2 + \frac{R + K_p}{L}\thinspace s + \frac{K_i}{L}
$$

Compare coefficients with the standard second-order system $`s^2 + 2\zeta\omega_n s + \omega_n^2`$.

$$
\frac{R + K_p}{L} = 2\zeta\omega_n \qquad \cdots(1)
$$

$$
\frac{K_i}{L} = \omega_n^2 \qquad \cdots(2)
$$

From $`(1)`$,

$$
K_p = 2\zeta\omega_n L - R
$$

From $`(2)`$,

$$
K_i = \omega_n^2 L
$$

These are the gain computation formulas in `main.cpp`.

---

## 4. Discretization of the numerical integration

### 4.1 Electrical system — forward Euler method

The current state equation $`di/dt = (-Ri + v)/L`$ is discretized by the forward Euler method.

$$
i_{k+1} = i_k + \Delta t\thinspace \frac{-R\thinspace i_k + v_k}{L} = \left(1 - \frac{R}{L}\Delta t\right)i_k + \frac{\Delta t}{L}\thinspace v_k
$$

The stability condition is $`\left|1 - \frac{R}{L}\Delta t\right| \le 1`$, that is,

$$
0 \le \Delta t \le \frac{2L}{R}
$$

In this code, against $`2L/R = 2\ \text{ms}`$, $`\Delta t = 0.25\ \text{ms}`$ is used (a 1/8 margin).

### 4.2 Mechanical system — trapezoidal integration

Since the mechanical system responds slowly and errors accumulate readily, second-order-accurate trapezoidal integration is used.

$$
\omega_{k+1} = \omega_k + \frac{\Delta t}{2}\left(\left.\frac{d\omega}{dt}\right|_{k+1} + \left.\frac{d\omega}{dt}\right|_k\right)
$$

In the code, the derivative values of the current step and the previous step are averaged and integrated as follows.

```cpp
angular_vel_ += (diff_angular_vel_ + pre_diff_angular_vel_) · resolution_ / 2.0;
```

### 4.3 Reason for using different discretization schemes

- **Electrical system**: against the sampling period of 250 µs, the electrical
  time constant $`L/R = 1\ \text{ms}`$ leaves ample margin, so forward Euler poses
  no problem in either accuracy or stability
- **Mechanical system**: because the response is slow and integration runs for a
  long time, second-order-accurate trapezoidal integration is preferable to
  suppress error accumulation
- **PI controller integral term**: trapezoidal integration achieves unbiased
  discrete integration

---

## 5. Derivation of the LPF phase lag (sensorless)

The transfer function of a first-order low-pass filter is

$$
H(s) = \frac{\omega_c}{s + \omega_c}
$$

The phase lag for a sinusoidal signal of angular frequency $`\omega_e`$ is obtained by substituting $`s = j\omega_e`$,

$$
\angle H(j\omega_e) = -\arctan\negthinspace \left(\frac{\omega_e}{\omega_c}\right)
$$

In sensorless control, the back-EMF (angular frequency = electrical angular
velocity $`\omega_e`$) passes through this LPF, so the estimated angle lags the
true angle by $`\arctan(\omega_e/\omega_c)`$. `get_angle_deg()` adds this value to
compensate for the phase lag.

---

## Related documents

- [`theory/coordinate-transform.md`](theory/coordinate-transform.md)
- [`theory/pi-tuning.md`](theory/pi-tuning.md)
- [`theory/sensorless.md`](theory/sensorless.md)
