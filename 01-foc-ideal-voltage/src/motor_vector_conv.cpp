// =============================================================================
//  motor_vector_conv.cpp  —  座標変換ユーティリティ — 実装
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 01-foc-ideal-voltage
//  振幅不変形の Clarke / Park 変換と、線間電圧利用率を 2/√3 倍に
//  拡張する min-max 方式の中点変調を実装する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include "motor_vector_conv.hpp"

namespace {
    constexpr double kTwoPiThirds = 2.0 / 3.0 * std::numbers::pi;
}

// UVW (3-phase) -> dq (rotating frame), amplitude-invariant scaling
Eigen::Vector2d MotorVectorConv::uvw_to_dq(const Eigen::Vector3d& uvw, double deg)
{
    const double theta = deg * std::numbers::pi / 180.0;

    Eigen::Matrix<double, 2, 3> t;
    t(0, 0) = std::cos(theta);                 t(0, 1) = std::cos(theta + kTwoPiThirds); t(0, 2) = std::cos(theta - kTwoPiThirds);
    t(1, 0) = std::sin(theta);                 t(1, 1) = std::sin(theta + kTwoPiThirds); t(1, 2) = std::sin(theta - kTwoPiThirds);

    return (std::sqrt(2.0) / 3.0) * (t * uvw);
}

// dq (rotating frame) -> UVW (3-phase), amplitude-invariant scaling
Eigen::Vector3d MotorVectorConv::dq_to_uvw(const Eigen::Vector2d& dq, double deg)
{
    const double theta = deg * std::numbers::pi / 180.0;

    Eigen::Matrix<double, 3, 2> t;
    t(0, 0) = std::cos(theta);                 t(0, 1) = std::sin(theta);
    t(1, 0) = std::cos(theta + kTwoPiThirds);  t(1, 1) = std::sin(theta + kTwoPiThirds);
    t(2, 0) = std::cos(theta - kTwoPiThirds);  t(2, 1) = std::sin(theta - kTwoPiThirds);

    return std::sqrt(2.0) * (t * dq);
}

// Mid-point (zero-sequence) modulation -- "min-max" SVPWM.
// vzero = -(max(u,v,w) + min(u,v,w)) / 2 is added equally to all three phases.
// Line-to-line voltages are unchanged, so motor torque is unaffected, but the
// peak phase voltage is reduced, allowing ~15.5% higher fundamental amplitude
// within the same DC-link voltage.
Eigen::Vector3d MotorVectorConv::apply_midpoint_modulation(const Eigen::Vector3d& uvw)
{
    const double vmax = uvw.maxCoeff();
    const double vmin = uvw.minCoeff();
    const double vzero = -0.5 * (vmax + vmin);
    return uvw + Eigen::Vector3d::Constant(vzero);
}
