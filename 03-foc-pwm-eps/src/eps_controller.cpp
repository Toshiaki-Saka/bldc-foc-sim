// =============================================================================
//  eps_controller.cpp  —  EPS アシスト制御 — 実装
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 03-foc-pwm-eps
//  トーションバー検出トルクに対する V カーブのアシストマップを実装する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include "eps_controller.hpp"
#include <algorithm>
#include <cmath>

void EpsController::init(const EpsControllerConfig& cfg) {
    deadzone_ = cfg.deadzone;
    gain_     = cfg.gain;
    iq_max_   = cfg.iq_max;
}

double EpsController::compute_iq_ref(double sensor_torque) const {
    const double abs_t = std::abs(sensor_torque);
    if (abs_t <= deadzone_)
        return 0.0;
    const double sign = (sensor_torque > 0.0) ? 1.0 : -1.0;
    const double iq   = gain_ * (abs_t - deadzone_) * sign;
    return std::clamp(iq, -iq_max_, iq_max_);
}
