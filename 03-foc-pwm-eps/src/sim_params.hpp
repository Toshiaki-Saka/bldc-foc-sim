#pragma once
// =============================================================================
//  sim_params.hpp  —  モータ物理定数・シミュレーション設定
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 03-foc-pwm-eps
//  モータの電気/機械パラメータ、サンプリング周期、PI 制御の設計パラメータ
//  (自然角周波数・減衰比)、PWM・センサーレス関連の定数を一元定義する。
//  これらの値を変更することでシミュレーション条件を調整できる。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include <numbers>

// =============================================================================
//  公開情報をベースにしたパラメータ値
// =============================================================================
//  本ファイルのモータ電気/機械諸元は以下の出典を組み合わせて構成しています。
//
//   [1] Pang, Jang, Lee, "Steering Wheel Torque Control of Electric Power
//       Steering by PD-Control", ICCAS 2005, Table 1.
//       電気系 (Kt, Ke, R, L) およびモータ慣性 J を採用。
//       https://2005.iccas.org/submission/paper/upload/2final_CEPS_ICCAS2005.pdf
//
//   [2] ATO 1kW BLDC Motor (110WDM06020-48V) datasheet.
//       DC リンク電圧 48 V、極対数 (4 pair pole) など機械諸元のリファレンス。
//       https://www.ato.com/Content/doc/bldc-motor-110mm-series/
//                          ATO-110WDM06020-24-48-72-96.pdf
//
//  これらは EPS 用 1kW 級三相ブラシレスモータの典型的な値で、シミュレーション
//  結果が実機の挙動オーダーと整合するように選定しています。各社モータで実機
//  値が異なる場合は本ファイルの値のみ差し替えれば対応できます。
// =============================================================================

// Simulation time settings
constexpr double kResolution = 0.00025; // 250 [usec]
constexpr double kCalcSpan   = 5.0;     // default 5 [sec]

// -----------------------------------------------------------------------------
//  Motor model parameters  (出典 [1] ICCAS 2005, Table 1)
// -----------------------------------------------------------------------------
//  Pole pair number is 4 (8-pole rotor). 出典 [2] ATO 110WDM06020.
constexpr double kKt = 0.0533; // Torque constant       [Nm/A]   (旧 3.5/85.0)
constexpr double kKe = 0.0533; // Back-EMF constant     [V·s/rad](旧 3.5/85.0)
constexpr double kR  = 0.1;    // Phase resistance      [Ω]      (旧 0.015)
constexpr double kL  = 0.0001; // Phase inductance      [H]      (旧 0.01)
constexpr double kB  = 1.0e-2 / (2.0 * std::numbers::pi); // Viscous damping [Nm·s/rad]
constexpr double kJ  = 3.5e-4; // Rotor inertia         [kg·m²] (旧 0.000053)

// Pole pair number (8-pole rotor -> 4 pole pairs). 出典 [2] ATO 110WDM06020.
// 電気角 = 機械角 × kPolePairs, 電気角速度 = 機械角速度 × kPolePairs.
constexpr double kPolePairs = 4.0; // pole pairs [-]

// Current controller tuning: natural frequency [rad/s] and damping ratio [-]
//  PIゲインは二次系極配置から導出 (main.cpp 参照):
//    Kp = 2·ζ·ωn·L − R,  Ki = ωn²·L
//  ζ = 1 で臨界制動となりオーバーシュートなし.
//  電気時定数 τ_e = L/R = 1 ms, サンプリング周期 250 μs に対し ωn·Ts = 0.25 で
//  離散化誤差は許容範囲内.
constexpr double kWn   = 1000.0; // natural frequency  [rad/s]
constexpr double kZeta = 1.00;   // damping ratio      [-]  → critically damped, no overshoot

// Default simulation conditions (overridable via CLI)
constexpr double kDefaultIqRef = 85.0; // [A]   定常で 0.0533·85 ≈ 4.5 Nm
constexpr double kDefaultTload = 4.3;  // [Nm]  定格トルク以下の負荷

// -----------------------------------------------------------------------------
//  PWM voltage output parameters
// -----------------------------------------------------------------------------
//  Vdc は出典 [2] ATO 110WDM06020-48V の定格電圧 48V に整合.
//  キャリア周波数 40 kHz, 最大デューティ95%, 最大Iq 125A は典型的なEPS-ECU値.
constexpr double kVdc              = 48.0;     // DC link voltage [V]
constexpr double kPwmMaxDuty       = 0.95;     // Maximum PWM duty cycle (at kPwmMaxAmp)
constexpr double kPwmMaxAmp        = 125.0;    // Q-axis current [A] at maximum duty cycle
constexpr double kPwmCarrierPeriod = 0.000025; // 25 [usec] = 40 kHz carrier
