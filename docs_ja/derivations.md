# 数式の導出

本ドキュメントは、`bldc-foc-sim` で用いる主要な数式の導出をまとめる。
各 theory ドキュメントから参照される補足資料である。

---

## 1. Clarke 変換 (三相 → αβ) の導出

三相巻線は空間的に 120° ずつずれて配置されている。U・V・W 各相の作る
起磁力ベクトルを、互いに直交する α・β の 2 軸に射影する。

U 相を α 軸に一致させると、各相軸の単位ベクトルは

$$
\hat{e}_U = (1,\ 0), \quad \hat{e}_V = \negthinspace \left(-\tfrac{1}{2},\ \tfrac{\sqrt{3}}{2}\right), \quad \hat{e}_W = \negthinspace \left(-\tfrac{1}{2},\ -\tfrac{\sqrt{3}}{2}\right)
$$

α・β 成分は各相量をこの軸方向に射影して足し合わせたものである。

$$
\alpha = U \cdot 1 + V \cdot \left(-\tfrac{1}{2}\right) + W \cdot \left(-\tfrac{1}{2}\right)
$$

$$
\beta  = U \cdot 0 + V \cdot \tfrac{\sqrt{3}}{2} + W \cdot \left(-\tfrac{\sqrt{3}}{2}\right)
$$

振幅不変とするためのスケール係数 $\tfrac{2}{3}$ を掛けると、Clarke 変換が得られる。

$$
\alpha = \frac{2}{3}\negthinspace \left(U - \frac{V}{2} - \frac{W}{2}\right), \qquad \beta  = \frac{2}{3}\negthinspace \left(\frac{\sqrt{3}}{2}V - \frac{\sqrt{3}}{2}W\right)
$$

三相平衡条件 $U + V + W = 0$ のとき、三相正弦波の振幅と αβ 量の振幅が
一致する。

---

## 2. Park 変換 (αβ → dq) の導出

αβ は静止座標系、dq はロータと同期して角度 $\theta$ で回転する座標系である。
回転座標系から見た成分は、静止座標系の量を $-\theta$ だけ回転させたものに
等しい。回転行列より

$$
d =  \alpha\cos\theta + \beta\sin\theta, \qquad q = -\alpha\sin\theta + \beta\cos\theta
$$

逆変換は $\theta$ だけ回転させればよい（回転行列の転置 = 逆行列）。

$$
\alpha = d\cos\theta - q\sin\theta, \qquad \beta  = d\sin\theta + q\cos\theta
$$

---

## 3. PI ゲインの極配置 (詳細導出)

電気系プラント（電圧 → 電流）は 1 次遅れ系である。

$$
G(s) = \frac{1}{Ls + R}
$$

PI 制御器は

$$
C(s) = K_p + \frac{K_i}{s} = \frac{K_p s + K_i}{s}
$$

開ループ伝達関数は

$$
C(s)\thinspace G(s) = \frac{K_p s + K_i}{s\thinspace (Ls + R)}
$$

閉ループ伝達関数 $T(s) = CG/(1 + CG)$ の分母多項式は

$$
s(Ls + R) + (K_p s + K_i) = Ls^2 + (R + K_p)s + K_i
$$

両辺を $L$ で割って正規化する。

$$
s^2 + \frac{R + K_p}{L}\thinspace s + \frac{K_i}{L}
$$

これを標準 2 次系 $s^2 + 2\zeta\omega_n s + \omega_n^2$ と係数比較する。

$$
\frac{R + K_p}{L} = 2\zeta\omega_n \qquad \cdots(1)
$$

$$
\frac{K_i}{L} = \omega_n^2 \qquad \cdots(2)
$$

$(1)$ より

$$
K_p = 2\zeta\omega_n L - R
$$

$(2)$ より

$$
K_i = \omega_n^2 L
$$

これが `main.cpp` のゲイン算出式である。

---

## 4. 数値積分の離散化

### 4.1 電気系 — 前進オイラー法

電流の状態方程式 $di/dt = (-Ri + v)/L$ を前進オイラー法で離散化する。

$$
i_{k+1} = i_k + \Delta t\thinspace \frac{-R\thinspace i_k + v_k}{L} = \left(1 - \frac{R}{L}\Delta t\right)i_k + \frac{\Delta t}{L}\thinspace v_k
$$

安定条件は $\left|1 - \frac{R}{L}\Delta t\right| \le 1$、すなわち

$$
0 \le \Delta t \le \frac{2L}{R}
$$

本コードでは $2L/R = 2\ \text{ms}$ に対し $\Delta t = 0.25\ \text{ms}$（1/8 の余裕）としている。

### 4.2 機械系 — 台形積分法

機械系は応答が遅く誤差が累積しやすいため、2 次精度の台形積分を用いる。

$$
\omega_{k+1} = \omega_k + \frac{\Delta t}{2}\left(\left.\frac{d\omega}{dt}\right|_{k+1} + \left.\frac{d\omega}{dt}\right|_k\right)
$$

コード上は次のように、今ステップと前ステップの微分値を平均して積分する。

```cpp
angular_vel_ += (diff_angular_vel_ + pre_diff_angular_vel_) · resolution_ / 2.0;
```

### 4.3 離散化方式を使い分ける理由

- **電気系** : サンプリング周期 250 µs に対し電気時定数 $L/R = 1\ \text{ms}$ と
  十分余裕があり、前進オイラーで精度・安定性とも問題ない
- **機械系** : 応答が遅く長時間積分するため、誤差累積を抑える 2 次精度の
  台形積分が望ましい
- **PI 制御器の積分項** : 台形積分でバイアスのない離散積分を実現する

---

## 5. LPF 位相遅れの導出 (センサーレス)

1 次ローパスフィルタの伝達関数は

$$
H(s) = \frac{\omega_c}{s + \omega_c}
$$

角周波数 $\omega_e$ の正弦波信号に対する位相遅れは、$s = j\omega_e$ を代入して

$$
\angle H(j\omega_e) = -\arctan\negthinspace \left(\frac{\omega_e}{\omega_c}\right)
$$

センサーレス制御では、誘起電圧（角周波数 = 電気角速度 $\omega_e$）がこの LPF を
通るため、推定角が真の角度より $\arctan(\omega_e/\omega_c)$ だけ遅れる。`get_angle_deg()`
はこの値を加算して位相遅れを補償する。

---

## 関連ドキュメント

- [`theory/coordinate-transform.md`](theory/coordinate-transform.md)
- [`theory/pi-tuning.md`](theory/pi-tuning.md)
- [`theory/sensorless.md`](theory/sensorless.md)
