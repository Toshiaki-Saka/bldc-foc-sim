#pragma once
// =============================================================================
//  motor_controller.hpp  —  FOC controller and PI controllers — declarations
// -----------------------------------------------------------------------------
//  Project : bldc-foc-sim / 01-foc-ideal-voltage
//  Declares the dq-axis PI controllers (PidController) and the FOC controller
//  (MotorController) that bundles them together to generate the three-phase
//  voltage commands. Midpoint modulation and dq-axis decoupling can be toggled
//  via run-time flags.
//
//  License : MIT (see LICENSE at repo root)
// =============================================================================

#include <Eigen/Dense>
#include "motor_vector_conv.hpp"
#include "sim_params.hpp"

enum class Axis { D = 0, Q = 1 };

struct PidConfig {
    double kp;
    double ki;
    double kd = 0.0;
    double output_max;
    double resolution;
};

struct AxisConfig {
    double kp;
    double ki;
    double kd = 0.0;
    double target_current;
    double max_current;
};

struct ControlOutput {
    Eigen::Vector3d phase_signal;
};

class PidController {
    double kp_          = 0.0;
    double ki_          = 0.0;
    double kd_          = 0.0;
    double output_max_  = 0.0;
    double resolution_  = 0.000250;
    double dev_p_       = 0.0;
    double dev_i_       = 0.0;
    double dev_d_       = 0.0;
    double prev_dev_p_  = 0.0;
    bool   initialized_ = false;

public:
    void                 init(const PidConfig& cfg);
    void                 update(double measurement, double setpoint);
    [[nodiscard]] double output() const;
};

class MotorController {
    PidController pid_d_;
    PidController pid_q_;
    double        target_d_ = 0.0;
    double        target_q_ = 85.0;
    // --- switchable feature flags (default OFF = legacy behaviour) ---
    bool use_midpoint_   = false; // mid-point (zero-sequence) modulation
    bool use_decoupling_ = false; // dq-axis decoupling (non-interacting control)

public:
    void init(Axis axis, const AxisConfig& cfg, double resolution);

    // Enable/disable mid-point modulation and dq decoupling at run time.
    void set_options(bool use_midpoint, bool use_decoupling) {
        use_midpoint_   = use_midpoint;
        use_decoupling_ = use_decoupling;
    }

    // Update the q-axis current reference at run time (used to inject a
    // transient via the --iq_step option).
    void set_target_q(double iq_ref) { target_q_ = iq_ref; }

    // compute() takes the measured 3-phase current, the electrical angle [deg]
    // and the electrical angular velocity [rad/s].  omega_elec is only used
    // when dq decoupling is enabled.
    [[nodiscard]] ControlOutput compute(const Eigen::Vector3d& current, double deg,
                                        double omega_elec = 0.0);
};
