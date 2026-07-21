# センサーレス制御 — 誘起電圧オブザーバと PLL

`04` / `05` モデルの **位置センサーレス制御** を説明する。コード上は `sensorless_observer.{hpp,cpp}` に対応する。

---

## 1. なぜ位置センサレスか

通常の FOC はロータ角度をレゾルバ等のセンサで測定する。これをセンサなしで推定する動機は次のとおり。

- **コスト削減** — レゾルバとそのインターフェース回路 (励磁・差動増幅・ADC) を省略できる
- **信頼性向上** — 機械的可動部が減り、故障モードが減る
- **小型化** — センサ取付スペースと配線が不要になる
- **冗長系** — レゾルバ故障時のバックアップ制御として併用できる

---

## 2. センサーレス制御の主要分類

| 方式 | 原理 | 適用域 |
|------|------|--------|
| 誘起電圧 (Back-EMF) ベース | 誘起電圧から角度を逆算 | 中速以上 |
| 高周波注入 (HFI) | 突極性を利用 | 低速・停止 (IPM 向き) |
| I-f 制御 | 電流ベクトルを強制回転 | 起動時の脱調防止 |
| 拡張カルマンフィルタ (EKF) | 状態推定の厳密版 | 全域 (計算負荷大) |

本コードは **誘起電圧オブザーバ方式** を採用する。中速以上で高精度だが、誘起電圧 $e = K_e \omega$ に比例するため、停止・低速域では推定精度が落ちる。

---

## 3. 誘起電圧オブザーバ

### 3.1 αβ 座標系での誘起電圧推定

モータの相端子電圧から、抵抗降下とインダクタンス由来の項を差し引くと、残りがロータ磁束による誘起電圧 (Back-EMF) となる。

$$
e = v - R i - L \frac{di}{dt}
$$

これを αβ 固定座標系で計算する (Clarke 変換のみで角度に依存しない)。

$$
e_\alpha = v_\alpha - R i_{\alpha,\text{prev}} - L \frac{i_\alpha - i_{\alpha,\text{prev}}}{dt}
$$

$$
e_\beta = v_\beta - R i_{\beta,\text{prev}} - L \frac{i_\beta - i_{\beta,\text{prev}}}{dt}
$$

**離散化の手順:**

1. 三相 → αβ 変換: $i_{\alpha\beta} =$ `uvw_to_alphabeta`$(i_{uvw})$、$v_{\alpha\beta} =$ `uvw_to_alphabeta`$(v_{uvw})$
2. 各軸で上式を適用して $e_\alpha,\thinspace  e_\beta$ を算出

### 3.2 離散微分の遅延補正

電圧 $v$ は 1 ステップ前の制御出力、電流 $i$ は今ステップの測定値である。離散微分項 $L(i - i_{\text{prev}})/dt$ は半ステップの遅延を含むため、抵抗降下項にも $i_{\text{prev}}$ を使って時間整合を取る。これはコード中の重要な工夫である。

### 3.3 ローパスフィルタによるノイズ除去

離散微分の影響で誘起電圧推定値はノイズを含む。1 次 LPF で平滑化する。

$$
e_{\alpha,\text{filt}} \mathrel{+}= (e_\alpha - e_{\alpha,\text{filt}}) \cdot \alpha_{\text{lpf}}, \qquad \alpha_{\text{lpf}} = 1 - e^{-\omega_c dt}
$$

本コードのカットオフは $\omega_c = 2000\thinspace \mathrm{rad/s}$ (約 318 Hz)。LPF は推定遅延と引き換えにノイズを低減する (トレードオフ)。

### 3.4 誘起電圧の規約と角度復元

本コードでは次の規約を用いる。

$$
e_\alpha = \frac{\sqrt{2}}{2} K_e \omega \sin\theta, \qquad e_\beta = \frac{\sqrt{2}}{2} K_e \omega \cos\theta
$$

この規約により $\theta = \mathrm{atan2}(e_\alpha,\thinspace  e_\beta)$ で角度を復元できる。ただし直接 ATAN2 すると角度がノイズでジャンプするため、次節の PLL を用いる。

---

## 4. PLL による角度・速度推定

**PLL (位相同期ループ)** は、内部に持つ推定角 $\hat{\theta}$ を誘起電圧の真の位相に「ロック」させる仕組みである。角度と速度を同時に推定できる。

### 4.1 クロスプロダクト誤差

誤差信号を次のように作る。

$$
\varepsilon = e_{\alpha,\text{filt}} \cos\hat{\theta} - e_{\beta,\text{filt}} \sin\hat{\theta} \approx C \sin(\theta_{\text{true}} - \hat{\theta})
$$

小角度近似で線形になるため、PI 制御で安定に 0 に収束させることができる。

### 4.2 PLL の閉ループ動作

$$
\varepsilon_i \mathrel{+}= \varepsilon \cdot dt \quad \text{(誤差の積分)}
$$

$$
\hat{\omega} = K_{p,\text{pll}} \varepsilon + K_{i,\text{pll}} \varepsilon_i \quad \text{(速度推定)}
$$

$$
\hat{\theta} \mathrel{+}= \hat{\omega} \cdot dt \quad \text{(角度更新)}
$$

最後に $\hat{\theta}$ を $[0,\thinspace  2\pi)$ に折り返す。

### 4.3 PLL ゲインと帯域

本コードの設定値:

| パラメータ | 値 | 意味 |
|-----------|-----|------|
| $K_{p,\text{pll}}$ | 500 [rad/s/V] | 比例ゲイン |
| $K_{i,\text{pll}}$ | 100000 [rad/s²/V] | 積分ゲイン |
| PLL 帯域 | $\approx \sqrt{K_{i,\text{pll}}} \approx 316\thinspace \mathrm{rad/s}$ (約 50 Hz) | |

PLL 帯域は LPF カットオフ (2000 rad/s) より十分低く設定し、フィルタ後の誘起電圧を安定に追従する。

### 4.4 LPF 位相遅れの補償

LPF は電気角速度 $\omega_e$ の信号を

$$
\varphi = \arctan\negthinspace \left(\frac{\omega_e}{\omega_c}\right)
$$

だけ遅らせる。誘起電圧がこの分だけ遅れるため、推定角は真の角度より $\varphi$ だけ遅れる。`get_angle_deg()` はこの位相遅れを $+\varphi$ 加算して補償し、定常角度誤差を小さく抑える。

---

## 5. センサーレスによる定常値の変化

005 モデルでは dq 変換に真の電気角ではなく推定角度 $\hat{\theta}$ を使う。LPF の位相遅れにより、定常状態でも

$$
\Delta\theta \approx -\arctan\negthinspace \left(\frac{\omega_e}{\omega_c}\right)
$$

の角度ズレが残る。例えば $\omega_e = 100\thinspace \mathrm{rad/s}$ なら $\Delta\theta \approx -2.86°$ である。

この $\Delta\theta$ により、PI が制御する dq 軸が「真の dq 軸」から少し回転しており、電流が以下のように分解される。

$$
i_q^{\text{true}} = i_q^{\text{est}} \cos(\Delta\theta) - i_d^{\text{est}} \sin(\Delta\theta)
$$

$$
i_d^{\text{true}} = i_q^{\text{est}} \sin(\Delta\theta) + i_d^{\text{est}} \cos(\Delta\theta)
$$

PI 制御は $i_q^{\text{est}} = 85\thinspace \mathrm{A}$、$i_d^{\text{est}} = 0$ に追従させるため、$\Delta\theta = 2.86°$ のとき:

$$
i_q^{\text{true}} \approx 85 \times \cos(2.86°) \approx 84.89\thinspace \mathrm{A} \quad \text{(約 0.12 ％ 減)}
$$

$$
i_d^{\text{true}} \approx 85 \times \sin(2.86°) \approx 4.24\thinspace \mathrm{A} \quad \text{(本来 0 のはずが漏れる)}
$$

LPF カットオフ $\omega_c$ を上げれば $\Delta\theta$ は減るが、ノイズ感度が悪化するトレードオフがある。

---

## 6. 起動シーケンス

### 6.1 低速・停止域の課題

誘起電圧オブザーバは $e = K_e \omega$ なので、$\omega \to 0$ では推定が破綻する。実機の真のセンサーレス制御では、低速・停止域を V/f 強制ランプ・I-f 制御・HFI・初期位置推定などでカバーする。

### 6.2 本コードのアプローチ — シードあり起動

本コードは上記の低速専用ロジックを実装せず、「教師あり助走 → 純粋センサーレス」のハイブリッド方式を採る。

| ステップ | 内容 |
|----------|------|
| Step 1 | 起動から 250 ms (`kStartupSteps = 1000`) は真のロータ角を観測器に注入: `observer.force_sync(true_elec_deg, true_omega_elec)` |
| Step 2 | それ以降は `est_deg = observer.get_angle_deg(omega_elec)` で純粋センサーレス制御に切替 |

### 6.3 ブレンド遷移による立ち上がり改善

シードから純粋センサーレスへハードに切り替えると、推定角がわずかにずれている分だけ dq 座標系が不連続にジャンプし、トルク波形に段差が出る。`kBlendSteps` (本コードでは 50 ms 相当) かけて真値から推定値へ線形にブレンドすることでこれを解消する。

> **`force_sync` に渡す速度について**
> PLL は電気角を積分するため、`force_sync` の速度引数には機械角速度ではなく **電気角速度** (= 機械角速度 × 極対数) を渡す必要がある。

---

## 7. コード構成 (005 プロジェクト)

| ファイル | 役割 |
|----------|------|
| `src/sensorless_observer.{cpp,hpp}` | オブザーバ + PLL 本体 |
| `src/motor_vector_conv.*` | Clarke 変換 (`uvw_to_alphabeta` 追加) |
| `src/main.cpp` | 起動シーケンス制御 (force_sync → 自立切替) |
| `src/sim_params.hpp` | `kObsLpfCutoff`, `kPllKp`, `kPllKi`, `kStartupSteps` を定義 |

---

## 関連ドキュメント

- [`coordinate-transform.md`](coordinate-transform.md) — Clarke 変換 (αβ)
- [`motor-model.md`](motor-model.md) — 誘起電圧を含む電圧方程式
- [`foc.md`](foc.md) — ベクトル制御 (FOC) の原理
- [`waveform-analysis.md`](waveform-analysis.md) — 実測ベースの波形差解析
