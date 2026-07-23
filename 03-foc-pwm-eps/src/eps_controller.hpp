#pragma once
// =============================================================================
//  eps_controller.hpp  —  EPS assist control — declarations
// -----------------------------------------------------------------------------
//  Project     : bldc-foc-sim / 03-foc-pwm-eps
//  Declares the class representing the assist map (V-curve) that generates the
//  q-axis current command from the steering torque.
//
//  License     : Apache-2.0 (see LICENSE at repo root)
// =============================================================================

struct EpsControllerConfig {
    double deadzone; // Torque sensor dead zone [Nm]
    double gain;     // Assist gain [A/Nm] above dead zone
    double iq_max;   // Maximum q-axis current [A]
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

    void                 init(const EpsControllerConfig& cfg);
    [[nodiscard]] double compute_iq_ref(double sensor_torque) const;
};
