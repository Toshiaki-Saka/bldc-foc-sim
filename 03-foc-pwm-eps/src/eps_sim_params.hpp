#pragma once
// =============================================================================
//  eps_sim_params.hpp  —  EPS 機構の物理定数
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 03-foc-pwm-eps
//  ステアリングコラム慣性、トーションバー剛性・減衰、減速ギア比、
//  ラック質量、アシストマップ係数など EPS 機構固有の定数を定義する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include <numbers>
#include "sim_params.hpp"

// =============================================================================
//  EPS 機構諸元 — 公開情報ベース
// =============================================================================
//  本ファイルの EPS 機構諸元は以下の出典を主に参照しています。
//
//   [1] Pang, Jang, Lee, "Steering Wheel Torque Control of Electric Power
//       Steering by PD-Control", ICCAS 2005, Table 1.
//       コラム式EPS (CEPS) の代表値: J_SW, M_R, R_P 他.
//       https://2005.iccas.org/submission/paper/upload/2final_CEPS_ICCAS2005.pdf
//
//  ICCAS 2005 はコラム式EPS (C-EPS, 減速比 N1=49/3≈16.33) の例ですが、
//  本シミュレーションは「モータ→ピニオン直結 + 小減速ギア」型 (R-EPS/P-EPS
//  系) を想定しており、ギア比のみは設計上の動作点を維持するため独自値を採用
//  しています。これにより本ファイルの kEpsGearRatio を ICCAS の N1=49/3 に
//  差し替えれば C-EPS シミュレーションに切り替え可能です。
// =============================================================================

// -----------------------------------------------------------------------------
//  EPS gearbox
// -----------------------------------------------------------------------------
constexpr double kEpsMaxAssistTorque  = 9.5;    // [Nm] ピニオン側 最大アシストトルク
// Gear ratio derived so that Ng * Kt * Iq_max == kEpsMaxAssistTorque
//   設計動作点の維持を優先し、本シミュレーションでは小減速ギア型を採用.
//   C-EPS (コラム式) を想定する場合は ICCAS 2005 の N1=49/3≈16.33 に差し替え.
constexpr double kEpsGearRatio        = kEpsMaxAssistTorque / (kKt * kDefaultIqRef);
                                        // 9.5 / (0.0533 * 85) ≈ 2.097

// -----------------------------------------------------------------------------
//  Torsion bar (torque sensor compliance)
// -----------------------------------------------------------------------------
//  実機トルクセンサの典型値 (1.5–2.5 Nm/deg) に整合させた値を採用。
//  ICCAS 2005 の K_TR=42057 Nm/rad は減速ギアまで含めた等価剛性で、
//  トルクセンサ単体のコンプライアンスとは性質が異なるため別扱い。
constexpr double kTorsionBarStiffness = 2.5 * 180.0 / std::numbers::pi;  // 2.5 Nm/deg → ≈143.24 Nm/rad
// ζ_sw = Ctb / (2*sqrt(Ktb*Jsw)) → Ctb=2.0 で ζ≈0.42 (機械共振 9.5Hz を抑制)
constexpr double kTorsionBarDamping   = 2.0;    // [Nm·s/rad]

// -----------------------------------------------------------------------------
//  Steering wheel & column inertia  (出典 [1] ICCAS 2005)
// -----------------------------------------------------------------------------
constexpr double kJsw      = 0.03444;   // [kg·m²] J_SW (旧 0.04)
// Lower column base inertia (excluding motor and rack)
//   ICCAS 2005 の J_SC=0.03444 はステアリングコラム単体相当. 本モデルでは
//   モータ/ラック慣性を別途持つため、ベース慣性のみとして 1/N²側成分を除外.
constexpr double kJcolBase = 0.002;     // [kg·m²] (実装ノート: 旧値維持)

// -----------------------------------------------------------------------------
//  Pinion and rack  (出典 [1] ICCAS 2005)
// -----------------------------------------------------------------------------
constexpr double kPinionRadius     = 0.007367; // [m]  R_P (旧 0.008)
constexpr double kRackMass         = 2.0;      // [kg] M_R (旧 0.5)
// ラックに付加する仮想バネ・ダンパ (路面反力を簡易表現)
constexpr double kRackSpringConst  = 80000.0;  // [N/m]  (実装値、旧値維持)
constexpr double kRackDampingConst = 500.0;    // [N·s/m] (実装値、旧値維持)

// -----------------------------------------------------------------------------
//  EPS controller (assist map)
// -----------------------------------------------------------------------------
constexpr double kEpsDeadzone   = 0.3;   // [Nm] torque sensor dead zone
constexpr double kEpsAssistGain = 18.0;  // [A/Nm] Iq per sensor torque above dead zone
constexpr double kEpsIqMax      = kDefaultIqRef;  // [A] = 85 A

// ECU torque sensor low-pass filter (must be below 9.5 Hz mechanical resonance)
constexpr double kEpsSensorLpfOmega = 20.0;  // [rad/s] ≈ 3.2 Hz

// -----------------------------------------------------------------------------
//  Simulation
// -----------------------------------------------------------------------------
constexpr double kEpsCalcSpan      = 5.0;  // [s] total simulation duration
constexpr double kEpsHandTorqueMax = 5.0;  // [Nm] peak driver input torque
constexpr double kEpsRampDuration  = 2.0;  // [s] ramp from 0 to kEpsHandTorqueMax
