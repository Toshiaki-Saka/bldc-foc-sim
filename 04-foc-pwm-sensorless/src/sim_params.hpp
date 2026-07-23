#pragma once
// =============================================================================
//  sim_params.hpp  —  motor physical constants / simulation settings
// -----------------------------------------------------------------------------
//  Project : bldc-foc-sim / 04-foc-pwm-sensorless
//  Centrally defines the motor electrical/mechanical parameters, the sampling
//  period, the PI control design parameters (natural angular frequency and
//  damping ratio), and the PWM- and sensorless-related constants.
//  Adjust the simulation conditions by changing these values.
//
//  License : Apache-2.0 (see LICENSE at repo root)
// =============================================================================

#include <numbers>

// =============================================================================
//  Parameter values based on publicly available information
// =============================================================================
//  The motor electrical/mechanical specifications in this file are assembled
//  by combining the following sources.
//
//   [1] Pang, Jang, Lee, "Steering Wheel Torque Control of Electric Power
//       Steering by PD-Control", ICCAS 2005, Table 1.
//       Electrical parameters (Kt, Ke, R, L) and the motor inertia J are taken
//       from here.
//       https://2005.iccas.org/submission/paper/upload/2final_CEPS_ICCAS2005.pdf
//
//   [2] ATO 1kW BLDC Motor (110WDM06020-48V) datasheet.
//       Reference for the mechanical specifications such as the DC-link voltage
//       48 V and the number of pole pairs (4 pole pairs).
//       https://www.ato.com/Content/doc/bldc-motor-110mm-series/
//                          ATO-110WDM06020-24-48-72-96.pdf
//
//  These are typical values for a 1kW-class three-phase brushless (BLDC/PMSM)
//  motor used in EPS, chosen so that the simulation results are consistent with
//  the order of magnitude of real hardware behavior. If the actual values
//  differ for another vendor's motor, only the values in this file need to be
//  replaced.
// =============================================================================

// Simulation time settings
constexpr double kResolution = 0.00025; // 250 [usec]
constexpr double kCalcSpan   = 5.0;     // default 5 [sec]

// -----------------------------------------------------------------------------
//  Motor model parameters  (source [1] ICCAS 2005, Table 1)
// -----------------------------------------------------------------------------
//  Pole pair number is 4 (8-pole rotor). Source [2] ATO 110WDM06020.
constexpr double kKt = 0.0533; // Torque constant       [Nm/A]   (was 3.5/85.0)
constexpr double kKe = 0.0533; // Back-EMF constant     [V·s/rad](was 3.5/85.0)
constexpr double kR  = 0.1;    // Phase resistance      [Ω]      (was 0.015)
constexpr double kL  = 0.0001; // Phase inductance      [H]      (was 0.01)
constexpr double kB  = 1.0e-2 / (2.0 * std::numbers::pi); // Viscous damping [Nm·s/rad]
constexpr double kJ  = 3.5e-4; // Rotor inertia         [kg·m²] (was 0.000053)

// Pole pair number (8-pole rotor -> 4 pole pairs). Source [2] ATO 110WDM06020.
// electrical angle = mechanical angle * kPolePairs,
// electrical angular velocity = mechanical angular velocity * kPolePairs.
constexpr double kPolePairs = 4.0; // pole pairs [-]

// Current controller tuning: natural frequency [rad/s] and damping ratio [-]
//  The PI gains are derived from second-order pole placement (see main.cpp):
//    Kp = 2·ζ·ωn·L − R,  Ki = ωn²·L
//  With ζ = 1 the response is critically damped with no overshoot.
//  For the electrical time constant τ_e = L/R = 1 ms and a sampling period of
//  250 μs, ωn·Ts = 0.25, so the discretization error stays within an
//  acceptable range.
constexpr double kWn   = 1000.0; // natural frequency  [rad/s]
constexpr double kZeta = 1.00;   // damping ratio      [-]  → critically damped, no overshoot

// Default simulation conditions (overridable via CLI)
constexpr double kDefaultIqRef = 85.0; // [A]   at steady state 0.0533·85 ≈ 4.5 Nm
constexpr double kDefaultTload = 4.3;  // [Nm]  load below the rated torque

// -----------------------------------------------------------------------------
//  PWM voltage output parameters
// -----------------------------------------------------------------------------
//  Vdc matches the rated voltage 48V of source [2] ATO 110WDM06020-48V.
//  Carrier frequency 40 kHz, max duty 95%, and max Iq 125A are typical EPS-ECU values.
constexpr double kVdc              = 48.0;     // DC link voltage [V]
constexpr double kPwmMaxDuty       = 0.95;     // Maximum PWM duty cycle (at kPwmMaxAmp)
constexpr double kPwmMaxAmp        = 125.0;    // Q-axis current [A] at maximum duty cycle
constexpr double kPwmCarrierPeriod = 0.000025; // 25 [usec] = 40 kHz carrier

// -----------------------------------------------------------------------------
//  Sensorless back-EMF observer parameters
// -----------------------------------------------------------------------------
//  LPF cutoff 500 rad/s: back-EMF noise rejection (>3x electrical freq ~144 rad/s)
//  PLL natural frequency wn = sqrt(C*Ki) ~= 233 rad/s  (C = (sqrt2/2)*Ke*w_ss ~= 5.4 V)
//  Damping ratio zeta = C*Kp/(2*wn) ~= 1.16  -> over-damped, stable tracking
constexpr double kObsLpfCutoff = 2000.0;   // back-EMF LPF cutoff frequency [rad/s]
constexpr double kPllKp        = 500.0;    // PLL proportional gain  [rad/s / V]
constexpr double kPllKi        = 100000.0; // PLL integral gain      [rad/s^2 / V]

// Seeded startup: observer is force-synced with true angle for the first kStartupSteps
// so that the BEMF filter reaches steady state before switching to blind sensorless mode.
// This mirrors the open-loop V/f ramp used in real sensorless drives.
constexpr int kStartupSteps = 1000; // 250 ms seeded startup (at 250 us/step)

// After the seeded-startup window the estimator is blended from the true angle
// to the estimated angle over kBlendSteps steps.  A hard switch would cause a
// step change in the dq frame (and hence a torque glitch); the linear blend
// makes the transition smooth.  200 steps = 50 ms at 250 us/step.
constexpr int kBlendSteps = 200;
