#pragma once
// =============================================================================
//  eps_sim_params.hpp  —  EPS mechanism physical constants
// -----------------------------------------------------------------------------
//  Project     : bldc-foc-sim / 03-foc-pwm-eps
//  Defines constants specific to the EPS mechanism, such as steering column
//  inertia, torsion bar stiffness/damping, reduction gear ratio, rack mass,
//  and assist map coefficients.
//
//  License     : MIT (see LICENSE at repo root)
// =============================================================================

#include <numbers>
#include "sim_params.hpp"

// =============================================================================
//  EPS mechanism specifications — based on public information
// =============================================================================
//  The EPS mechanism specifications in this file mainly reference the
//  following source.
//
//   [1] Pang, Jang, Lee, "Steering Wheel Torque Control of Electric Power
//       Steering by PD-Control", ICCAS 2005, Table 1.
//       Representative values for column-type EPS (CEPS): J_SW, M_R, R_P, etc.
//       https://2005.iccas.org/submission/paper/upload/2final_CEPS_ICCAS2005.pdf
//
//  ICCAS 2005 is an example of column-type EPS (C-EPS, reduction ratio
//  N1=49/3≈16.33), but this simulation assumes a "motor -> pinion direct-drive
//  + small reduction gear" type (R-EPS/P-EPS family). Only the gear ratio uses
//  an independent value in order to maintain the design operating point.
//  Because of this, the simulation can be switched to C-EPS by replacing
//  kEpsGearRatio in this file with ICCAS's N1=49/3.
// =============================================================================

// -----------------------------------------------------------------------------
//  EPS gearbox
// -----------------------------------------------------------------------------
constexpr double kEpsMaxAssistTorque = 9.5; // [Nm] max assist torque on the pinion side
// Gear ratio derived so that Ng * Kt * Iq_max == kEpsMaxAssistTorque
//   Prioritizing maintenance of the design operating point, this simulation
//   adopts a small reduction gear type.
//   To assume C-EPS (column type), replace with ICCAS 2005's N1=49/3≈16.33.
constexpr double kEpsGearRatio = kEpsMaxAssistTorque / (kKt * kDefaultIqRef);
// 9.5 / (0.0533 * 85) ≈ 2.097

// -----------------------------------------------------------------------------
//  Torsion bar (torque sensor compliance)
// -----------------------------------------------------------------------------
//  A value matched to the typical range of a real torque sensor (1.5–2.5 Nm/deg)
//  is adopted. ICCAS 2005's K_TR=42057 Nm/rad is the equivalent stiffness
//  including the reduction gear, which differs in nature from the compliance of
//  the torque sensor alone, so it is treated separately.
constexpr double kTorsionBarStiffness =
    2.5 * 180.0 / std::numbers::pi; // 2.5 Nm/deg → ≈143.24 Nm/rad
// ζ_sw = Ctb / (2*sqrt(Ktb*Jsw)) → with Ctb=2.0, ζ≈0.42 (suppresses the 9.5Hz mechanical resonance)
constexpr double kTorsionBarDamping = 2.0; // [Nm·s/rad]

// -----------------------------------------------------------------------------
//  Steering wheel & column inertia  (source [1] ICCAS 2005)
// -----------------------------------------------------------------------------
constexpr double kJsw = 0.03444; // [kg·m²] J_SW (old 0.04)
// Lower column base inertia (excluding motor and rack)
//   ICCAS 2005's J_SC=0.03444 corresponds to the steering column alone. Since
//   this model holds the motor/rack inertias separately, it takes only the base
//   inertia and excludes the 1/N²-side component.
constexpr double kJcolBase = 0.002; // [kg·m²] (implementation note: old value retained)

// -----------------------------------------------------------------------------
//  Pinion and rack  (source [1] ICCAS 2005)
// -----------------------------------------------------------------------------
constexpr double kPinionRadius = 0.007367; // [m]  R_P (old 0.008)
constexpr double kRackMass     = 2.0;      // [kg] M_R (old 0.5)
// Virtual spring/damper added to the rack (simplified representation of road reaction)
constexpr double kRackSpringConst  = 80000.0; // [N/m]  (implementation value, old value retained)
constexpr double kRackDampingConst = 500.0;   // [N·s/m] (implementation value, old value retained)

// -----------------------------------------------------------------------------
//  EPS controller (assist map)
// -----------------------------------------------------------------------------
constexpr double kEpsDeadzone   = 0.3;           // [Nm] torque sensor dead zone
constexpr double kEpsAssistGain = 18.0;          // [A/Nm] Iq per sensor torque above dead zone
constexpr double kEpsIqMax      = kDefaultIqRef; // [A] = 85 A

// ECU torque sensor low-pass filter (must be below 9.5 Hz mechanical resonance)
constexpr double kEpsSensorLpfOmega = 20.0; // [rad/s] ≈ 3.2 Hz

// -----------------------------------------------------------------------------
//  Simulation
// -----------------------------------------------------------------------------
constexpr double kEpsCalcSpan      = 5.0; // [s] total simulation duration
constexpr double kEpsHandTorqueMax = 5.0; // [Nm] peak driver input torque
constexpr double kEpsRampDuration  = 2.0; // [s] ramp from 0 to kEpsHandTorqueMax
