#pragma once
// =============================================================================
//  motor_vector_conv.hpp  —  座標変換ユーティリティ — 宣言
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 01-foc-ideal-voltage
//  Clarke 変換 (三相 UVW → 二相 αβ)、Park 変換 (αβ → 回転 dq)、
//  および中点変調 (零相注入 SVPWM) の静的関数を宣言する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include <cmath>
#include <numbers>
#include <Eigen/Dense>

// Stateless Clarke/Park transform utilities for a 3-phase AC motor.
class MotorVectorConv {
public:
    [[nodiscard]] static Eigen::Vector2d uvw_to_dq(const Eigen::Vector3d& uvw, double deg);
    [[nodiscard]] static Eigen::Vector3d dq_to_uvw(const Eigen::Vector2d& dq,  double deg);

    // Mid-point (zero-sequence) modulation.
    // Injects a common-mode offset equal to -(max+min)/2 of the three phase
    // voltages.  This is the "min-max" form of Space Vector PWM (SVPWM) and
    // extends the usable line-to-line voltage by a factor of 2/sqrt(3) (~15.5%)
    // without affecting the line-to-line voltages (and hence the motor torque).
    [[nodiscard]] static Eigen::Vector3d apply_midpoint_modulation(const Eigen::Vector3d& uvw);
};
