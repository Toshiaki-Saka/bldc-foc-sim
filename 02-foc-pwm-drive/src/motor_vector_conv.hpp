#pragma once
// =============================================================================
//  motor_vector_conv.hpp  —  座標変換ユーティリティ — 宣言
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 02-foc-pwm-drive
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
    // Midpoint (zero-sequence) modulation: shifts the 3-phase voltage so that
    // the min/max are centered, extending linear DC-bus utilization by 2/sqrt(3)
    // (~15%). Equivalent to SVPWM / third-harmonic injection.
    [[nodiscard]] static Eigen::Vector3d apply_midpoint_modulation(const Eigen::Vector3d& uvw);
};
