// =============================================================================
//  motor_vector_conv.cpp  —  coordinate transform utility — implementation
// -----------------------------------------------------------------------------
//  Project      : bldc-foc-sim (shared across all models)
//  Implements the amplitude-invariant Clarke / Park transforms and the min-max
//  midpoint modulation that extends the line-voltage utilization by a factor of
//  2/sqrt(3).
//
//  NOTE: This file is identical across all models (01-05). When changing it,
//        propagate the change to every model. The CI (consistency job) checks
//        cross-model equality and detects drift.
//
//  License      : Apache-2.0 (see LICENSE at repo root)
// =============================================================================

#include "motor_vector_conv.hpp"

namespace {
constexpr double kTwoPiThirds = 2.0 / 3.0 * std::numbers::pi;
}

// UVW -> αβ (stationary frame): Clarke transform, amplitude-invariant (= uvw_to_dq at θ=0)
Eigen::Vector2d MotorVectorConv::uvw_to_alphabeta(const Eigen::Vector3d& uvw) {
    return uvw_to_dq(uvw, 0.0);
}

// UVW (3-phase) -> dq (rotating frame), amplitude-invariant scaling
Eigen::Vector2d MotorVectorConv::uvw_to_dq(const Eigen::Vector3d& uvw, double deg) {
    const double theta = deg * std::numbers::pi / 180.0;

    Eigen::Matrix<double, 2, 3> t;
    t(0, 0) = std::cos(theta);
    t(0, 1) = std::cos(theta + kTwoPiThirds);
    t(0, 2) = std::cos(theta - kTwoPiThirds);
    t(1, 0) = std::sin(theta);
    t(1, 1) = std::sin(theta + kTwoPiThirds);
    t(1, 2) = std::sin(theta - kTwoPiThirds);

    return (std::sqrt(2.0) / 3.0) * (t * uvw);
}

// dq (rotating frame) -> UVW (3-phase), amplitude-invariant scaling
Eigen::Vector3d MotorVectorConv::dq_to_uvw(const Eigen::Vector2d& dq, double deg) {
    const double theta = deg * std::numbers::pi / 180.0;

    Eigen::Matrix<double, 3, 2> t;
    t(0, 0) = std::cos(theta);
    t(0, 1) = std::sin(theta);
    t(1, 0) = std::cos(theta + kTwoPiThirds);
    t(1, 1) = std::sin(theta + kTwoPiThirds);
    t(2, 0) = std::cos(theta - kTwoPiThirds);
    t(2, 1) = std::sin(theta - kTwoPiThirds);

    return std::sqrt(2.0) * (t * dq);
}

// Midpoint (zero-sequence) modulation.
// Computes the zero-sequence offset vsn = -(max+min)/2 and adds it to all three
// phases. The line-to-line voltages are unchanged (the offset is common-mode),
// but the peak phase voltage required for a given line voltage shrinks, so the
// linear modulation range extends from Vdc/2 to Vdc/sqrt(3) (2/sqrt(3) ~ 1.155x).
// This is mathematically equivalent to space-vector PWM (SVPWM).
Eigen::Vector3d MotorVectorConv::apply_midpoint_modulation(const Eigen::Vector3d& uvw) {
    const double vmax   = uvw.maxCoeff();
    const double vmin   = uvw.minCoeff();
    const double offset = -0.5 * (vmax + vmin);
    return uvw + Eigen::Vector3d::Constant(offset);
}
