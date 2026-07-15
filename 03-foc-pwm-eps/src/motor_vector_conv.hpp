#pragma once
// =============================================================================
//  motor_vector_conv.hpp  —  coordinate transform utility — declarations
// -----------------------------------------------------------------------------
//  Project     : bldc-foc-sim (common to all models)
//  Declares the static functions for the Clarke transform (three-phase UVW ->
//  two-phase αβ), the Park transform (αβ -> rotating dq), and midpoint
//  modulation (zero-sequence-injection SVPWM).
//
//  * This file is identical across all models (01–05). When changing it,
//    reflect the change in all models. CI (the consistency job) checks the
//    match between models and detects drift.
//
//  License     : MIT (see LICENSE at repo root)
// =============================================================================

#include <cmath>
#include <numbers>
#include <Eigen/Dense>

// Stateless Clarke/Park transform utilities for a 3-phase AC motor.
class MotorVectorConv {
public:
    // Clarke transform: UVW -> αβ stationary frame (amplitude-invariant)
    [[nodiscard]] static Eigen::Vector2d uvw_to_alphabeta(const Eigen::Vector3d& uvw);
    // Combined Clarke + Park: UVW -> dq rotating frame
    [[nodiscard]] static Eigen::Vector2d uvw_to_dq(const Eigen::Vector3d& uvw, double deg);
    [[nodiscard]] static Eigen::Vector3d dq_to_uvw(const Eigen::Vector2d& dq, double deg);
    // Midpoint (zero-sequence) modulation: shifts the 3-phase voltage so that
    // the min/max are centered, extending linear DC-bus utilization by 2/sqrt(3)
    // (~15%). Equivalent to SVPWM / third-harmonic injection.
    [[nodiscard]] static Eigen::Vector3d apply_midpoint_modulation(const Eigen::Vector3d& uvw);
};
