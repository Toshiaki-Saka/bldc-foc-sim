#pragma once
// =============================================================================
//  eps_sim_params.hpp  —  Physical constants of the EPS mechanism
// -----------------------------------------------------------------------------
//  Project    : bldc-foc-sim / 05-foc-pwm-eps-sensorless
//  Defines constants specific to the EPS mechanism such as steering column
//  inertia, torsion bar stiffness/damping, reduction gear ratio, rack mass,
//  and assist map coefficients.
//
//  License    : MIT (see LICENSE at repo root)
// =============================================================================

#include <numbers>
#include "sim_params.hpp"

// =============================================================================
//  EPS mechanism specifications — based on public information
// =============================================================================
//  The EPS mechanism specifications in this file primarily reference the
//  following source.
//
//   [1] Pang, Jang, Lee, "Steering Wheel Torque Control of Electric Power
//       Steering by PD-Control", ICCAS 2005, Table 1.
//       Representative values for column-type EPS (CEPS): J_SW, M_R, R_P, etc.
//       https://2005.iccas.org/submission/paper/upload/2final_CEPS_ICCAS2005.pdf
//
//  ICCAS 2005 is an example of column-type EPS (C-EPS, reduction ratio
//  N1=49/3≈16.33), but this simulation assumes a "motor→pinion direct-drive +
//  small reduction gear" type (R-EPS/P-EPS family), and adopts an independent
//  value for the gear ratio alone in order to maintain the design operating
//  point. Because of this, replacing kEpsGearRatio in this file with the ICCAS
//  N1=49/3 lets you switch over to a C-EPS simulation.
// =============================================================================

// -----------------------------------------------------------------------------
//  EPS gearbox
// -----------------------------------------------------------------------------
constexpr double kEpsMaxAssistTorque = 9.5; // [Nm] max assist torque at the pinion
// Gear ratio derived so that Ng * Kt * Iq_max == kEpsMaxAssistTorque
//   Prioritizing maintenance of the design operating point, this simulation
//   adopts a small-reduction-gear type.
//   To assume C-EPS (column type), replace with ICCAS 2005's N1=49/3≈16.33.
constexpr double kEpsGearRatio = kEpsMaxAssistTorque / (kKt * kDefaultIqRef);
// 9.5 / (0.0533 * 85) ≈ 2.097

// -----------------------------------------------------------------------------
//  Torsion bar (torque sensor compliance)
// -----------------------------------------------------------------------------
//  A value consistent with the typical range of real torque sensors
//  (1.5–2.5 Nm/deg) is adopted.
//  ICCAS 2005's K_TR=42057 Nm/rad is an equivalent stiffness that also includes
//  the reduction gear, which differs in nature from the compliance of the torque
//  sensor alone, so it is treated separately.
constexpr double kTorsionBarStiffness =
    2.5 * 180.0 / std::numbers::pi; // 2.5 Nm/deg → ≈143.24 Nm/rad
// ζ_sw = Ctb / (2*sqrt(Ktb*Jsw)) → Ctb=2.0 gives ζ≈0.42 (suppresses the 9.5 Hz mechanical resonance)
constexpr double kTorsionBarDamping = 2.0; // [Nm·s/rad]

// -----------------------------------------------------------------------------
//  Steering wheel & column inertia  (source [1] ICCAS 2005)
// -----------------------------------------------------------------------------
constexpr double kJsw = 0.03444; // [kg·m²] J_SW (previously 0.04)
// Lower column base inertia (excluding motor and rack)
//   ICCAS 2005's J_SC=0.03444 corresponds to the steering column alone. Since
//   this model carries the motor/rack inertias separately, only the base
//   inertia is used here, excluding the 1/N²-side components.
constexpr double kJcolBase = 0.002; // [kg·m²] (implementation note: previous value retained)

// -----------------------------------------------------------------------------
//  Pinion and rack  (source [1] ICCAS 2005)
// -----------------------------------------------------------------------------
constexpr double kPinionRadius = 0.007367; // [m]  R_P (previously 0.008)
constexpr double kRackMass     = 2.0;      // [kg] M_R (previously 0.5)
// Virtual spring/damper attached to the rack (simplified representation of road reaction force)
constexpr double kRackSpringConst  = 80000.0; // [N/m]  (implementation value, previous value retained)
constexpr double kRackDampingConst = 500.0;   // [N·s/m] (implementation value, previous value retained)

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
