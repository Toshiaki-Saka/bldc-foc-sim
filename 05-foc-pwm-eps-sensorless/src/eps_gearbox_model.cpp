// =============================================================================
//  eps_gearbox_model.cpp  —  EPS mechanism dynamics model — implementation
// -----------------------------------------------------------------------------
//  Project    : bldc-foc-sim / 05-foc-pwm-eps-sensorless
//  Takes the driver steering torque and the motor torque as inputs, and updates
//  the column angle, rack displacement, and rack force by time integration.
//
//  License    : Apache-2.0 (see LICENSE at repo root)
// =============================================================================

#include "eps_gearbox_model.hpp"

void EpsGearboxModel::init(const EpsGearboxConfig& cfg) {
    jsw_ = cfg.jsw;
    // Reflect motor inertia and rack mass to the column/pinion shaft
    jcol_tot_ = cfg.jcol + cfg.jmotor * cfg.gear_ratio * cfg.gear_ratio +
                cfg.rack_mass * cfg.pinion_radius * cfg.pinion_radius;
    ktb_      = cfg.ktb;
    ctb_      = cfg.ctb;
    ng_       = cfg.gear_ratio;
    rp_       = cfg.pinion_radius;
    ks_       = cfg.spring_const;
    cs_       = cfg.damping_const;
    dt_       = cfg.resolution;

    theta_sw_  = 0.0;
    omega_sw_  = 0.0;
    theta_col_ = 0.0;
    omega_col_ = 0.0;
}

EpsGearboxState EpsGearboxModel::update(double hand_torque, double motor_torque) {
    // Torsion bar torque (= torque sensor reading)
    const double ttb = ktb_ * (theta_sw_ - theta_col_) + ctb_ * (omega_sw_ - omega_col_);

    // Rack state before integration
    const double x_rack = rp_ * theta_col_;
    const double v_rack = rp_ * omega_col_;
    // Spring + damper load on rack → moment about pinion shaft
    const double f_spring = ks_ * x_rack + cs_ * v_rack;
    const double t_spring = f_spring * rp_;

    // Assist torque at pinion delivered by motor via gearbox
    const double t_assist = ng_ * motor_torque;

    // Angular accelerations (Euler)
    const double alpha_sw  = (hand_torque - ttb) / jsw_;
    const double alpha_col = (ttb + t_assist - t_spring) / jcol_tot_;

    // Forward Euler integration
    omega_sw_ += alpha_sw * dt_;
    theta_sw_ += omega_sw_ * dt_;
    omega_col_ += alpha_col * dt_;
    theta_col_ += omega_col_ * dt_;

    // Updated rack state
    const double x_new = rp_ * theta_col_;
    const double v_new = rp_ * omega_col_;
    const double f_new = ks_ * x_new + cs_ * v_new;

    return EpsGearboxState{
        .theta_sw       = theta_sw_,
        .omega_sw       = omega_sw_,
        .theta_col      = theta_col_,
        .omega_col      = omega_col_,
        .rack_disp      = x_new,
        .rack_vel       = v_new,
        .rack_force     = f_new,
        .torsion_torque = ttb,
        .assist_torque  = t_assist,
    };
}
