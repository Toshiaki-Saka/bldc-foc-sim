#pragma once
// =============================================================================
//  sim_params.hpp  —  motor physical constants and simulation settings
// -----------------------------------------------------------------------------
//  Project : bldc-foc-sim / 01-foc-ideal-voltage
//  Centrally defines the motor electrical/mechanical parameters, the sampling
//  period, the PI control design parameters (natural angular frequency and
//  damping ratio), and the PWM/sensorless-related constants. The simulation
//  conditions can be adjusted by changing these values.
//
//  License : Apache-2.0 (see LICENSE at repo root)
// =============================================================================

#include <numbers>

// =============================================================================
//  Parameter values based on publicly available information
// =============================================================================
//  The motor electrical/mechanical specifications in this file are assembled
//  from a combination of the following sources.
//
//   [1] Pang, Jang, Lee, "Steering Wheel Torque Control of Electric Power
//       Steering by PD-Control", ICCAS 2005, Table 1.
//       Electrical parameters (Kt, Ke, R, L) and motor inertia J are taken
//       from here.
//       https://2005.iccas.org/submission/paper/upload/2final_CEPS_ICCAS2005.pdf
//
//   [2] ATO 1kW BLDC Motor (110WDM06020-48V) datasheet.
//       Reference for the mechanical size class, e.g. the number of pole pairs
//       (4 pole pairs).
//       https://www.ato.com/Content/doc/bldc-motor-110mm-series/
//                          ATO-110WDM06020-24-48-72-96.pdf
//
//  These are typical values for a 1kW-class three-phase brushless motor for
//  EPS, selected so that the simulation results match the order of magnitude of
//  real hardware behavior. If the real values differ for a given vendor's
//  motor, only the values in this file need to be replaced.
// =============================================================================

// Simulation time settings
constexpr double kResolution = 0.00025; // 250 [usec]
constexpr double kCalcSpan   = 5.0;     // default 5 [sec]

// -----------------------------------------------------------------------------
//  Motor model parameters  (source [1] ICCAS 2005, Table 1)
// -----------------------------------------------------------------------------
//  Pole pair number is 4 (8-pole rotor). Source [2] ATO 110WDM06020.
constexpr double kKt = 0.0533; // Torque constant       [Nm/A]   (old 3.5/85.0)
constexpr double kKe = 0.0533; // Back-EMF constant     [V·s/rad](old 3.5/85.0)
constexpr double kR  = 0.1;    // Phase resistance      [Ω]      (old 0.015)
constexpr double kL  = 0.0001; // Phase inductance      [H]      (old 0.01)
constexpr double kB  = 1.0e-2 / (2.0 * std::numbers::pi); // Viscous damping [Nm·s/rad]
constexpr double kJ  = 3.5e-4; // Rotor inertia         [kg·m²] (old 0.000053)

// Pole pair number (8-pole rotor -> 4 pole pairs). Source [2] ATO 110WDM06020.
// electrical angle = mechanical angle × kPolePairs,
// electrical angular velocity = mechanical angular velocity × kPolePairs.
constexpr double kPolePairs = 4.0; // pole pairs [-]

// Current controller tuning: natural frequency [rad/s] and damping ratio [-]
//  The PI gains are derived from second-order pole placement (see main.cpp):
//    Kp = 2·ζ·ωn·L − R,  Ki = ωn²·L
//  At ζ = 1 the system is critically damped with no overshoot.
//  With electrical time constant τ_e = L/R = 1 ms and sampling period 250 μs,
//  ωn·Ts = 0.25, so the discretization error is within the acceptable range.
constexpr double kWn   = 1000.0; // natural frequency  [rad/s]
constexpr double kZeta = 1.00;   // damping ratio      [-]  → critically damped, no overshoot

// Default simulation conditions (overridable via CLI)
constexpr double kDefaultIqRef = 85.0; // [A]   at steady state 0.0533·85 ≈ 4.5 Nm
constexpr double kDefaultTload = 4.3;  // [Nm]  load below the rated torque
