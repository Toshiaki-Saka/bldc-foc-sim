#pragma once
// =============================================================================
//  eps_controller.hpp  —  EPS アシスト制御 — 宣言
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 05-foc-pwm-eps-sensorless
//  操舵トルクから q 軸電流指令を生成するアシストマップ (V カーブ) を
//  表現するクラスを宣言する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

struct EpsControllerConfig {
    double deadzone;  // Torque sensor dead zone [Nm]
    double gain;      // Assist gain [A/Nm] above dead zone
    double iq_max;    // Maximum q-axis current [A]
};

// V-curve assist map: Iq_ref = clamp( gain * (|Tsensor| − deadzone) * sign(Tsensor), ±iq_max )
// Returns 0 inside the dead zone.
class EpsController {
    double deadzone_ = 0.3;
    double gain_     = 18.0;
    double iq_max_   = 85.0;

public:
    EpsController() = default;
    explicit EpsController(const EpsControllerConfig& cfg) { init(cfg); }

    void init(const EpsControllerConfig& cfg);
    [[nodiscard]] double compute_iq_ref(double sensor_torque) const;
};
