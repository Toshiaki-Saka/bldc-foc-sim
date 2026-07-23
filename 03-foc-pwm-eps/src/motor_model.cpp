// =============================================================================
//  motor_model.cpp  —  motor electrical and mechanical model (plant) — implementation
// -----------------------------------------------------------------------------
//  Project     : bldc-foc-sim / 03-foc-pwm-eps
//  Discretizes the electrical system with the forward Euler method and the
//  mechanical system with trapezoidal integration, updating the phase current,
//  electromagnetic torque, rotational speed, and angle by one step from the
//  applied voltage.
//
//  License     : Apache-2.0 (see LICENSE at repo root)
// =============================================================================

#include "motor_model.hpp"
#include <cmath>
#include <format>
#include <numbers>

/*** MotorModel ***/

void MotorModel::init(const MotorConfig& cfg) {
    inertia_            = cfg.inertia;
    coil_resistance_    = cfg.coil_resistance;
    counter_emf_        = cfg.counter_emf;
    torque_constant_    = cfg.torque_constant;
    viscous_resistance_ = cfg.viscous_resistance;
    inductance_         = cfg.inductance;
    resolution_         = cfg.resolution;
    pole_pairs_         = cfg.pole_pairs;

    load_torque_        = cfg.load_torque;
    vdc_                = cfg.vdc;
    csv_path_           = cfg.csv_path;
    pwm_csv_path_       = cfg.pwm_csv_path;
    pwm_carrier_period_ = cfg.pwm_carrier_period;
    mech_deg_           = cfg.initial_deg;
    elec_deg_           = cfg.initial_deg;
    pre_mech_deg_       = cfg.initial_deg;
}

MotorState MotorModel::update(const Eigen::Vector3d& input_voltage) {
    if (!csv_ready_) {
        csv_.open(csv_path_);
        csv_ << "U,V,W,ElecDeg,Te,id,iq,omega,Tm,MechDeg,AngleError,DutyU,DutyV,DutyW,Vu,Vv,Vw\n";
        csv_ready_ = true;
    }

    // UVW -> dq voltage
    const Eigen::Vector2d dq_voltage = MotorVectorConv::uvw_to_dq(input_voltage, elec_deg_);
    const double          d_voltage  = dq_voltage(0);
    const double          q_voltage  = dq_voltage(1);

    // Current dynamics (forward Euler)
    const double back_emf = counter_emf_ * angular_vel_;
    q_current_state_ +=
        (q_voltage - back_emf - coil_resistance_ * q_current_state_) / inductance_ * resolution_;
    d_current_state_ +=
        (d_voltage - coil_resistance_ * d_current_state_) / inductance_ * resolution_;

    const double d_current = d_current_state_;
    const double q_current = q_current_state_;

    // Torques
    const double elec_torque = q_current * torque_constant_;
    const double mech_torque = elec_torque - load_torque_ - viscous_resistance_ * pre_angular_vel_;

    // Angular velocity (trapezoidal integration)
    diff_angular_vel_ = mech_torque / inertia_;
    angular_vel_ += (diff_angular_vel_ + pre_diff_angular_vel_) * resolution_ / 2.0;

    // Mechanical angle [deg]
    mech_deg_ += (angular_vel_ + pre_angular_vel_) * resolution_ * 0.5 * (180.0 / std::numbers::pi);
    mech_deg_ = std::fmod(mech_deg_, 360.0);
    if (mech_deg_ < 0.0)
        mech_deg_ += 360.0;

    // Electrical angle tracking with low-pass correction
    auto wrap360 = [](double v) {
        v = std::fmod(v, 360.0);
        return v < 0.0 ? v + 360.0 : v;
    };
    auto wrap_diff = [](double d) -> double {
        if (d > 180.0)
            return d - 360.0;
        if (d < -180.0)
            return d + 360.0;
        return d;
    };

    const double mech_step = wrap_diff(mech_deg_ - pre_mech_deg_);
    elec_deg_ += mech_step * pole_pairs_;

    const double target = wrap360(mech_deg_ * pole_pairs_);
    elec_deg_ += 0.05 * wrap_diff(target - elec_deg_);
    elec_deg_ = wrap360(elec_deg_);

    const double angle_error = wrap_diff(target - elec_deg_);

    // dq actual current -> UVW phase current (state variables, not voltage)
    const Eigen::Vector2d dq_current_actual{d_current_state_, q_current_state_};
    const Eigen::Vector3d phase_current = MotorVectorConv::dq_to_uvw(dq_current_actual, elec_deg_);

    const double duty_u = 0.5 + input_voltage(0) / vdc_;
    const double duty_v = 0.5 + input_voltage(1) / vdc_;
    const double duty_w = 0.5 + input_voltage(2) / vdc_;

    csv_ << std::format("{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n", phase_current(0),
                        phase_current(1), phase_current(2), elec_deg_, elec_torque, d_current,
                        q_current, angular_vel_, mech_torque, mech_deg_, angle_error, duty_u,
                        duty_v, duty_w, input_voltage(0), input_voltage(1), input_voltage(2));

    // PWM waveform output: center-aligned (triangle carrier) at kPwmCarrierPeriod
    if (!pwm_csv_ready_) {
        pwm_csv_.open(pwm_csv_path_);
        pwm_csv_ << "Time_s,PwmU_V,PwmV_V,PwmW_V\n";
        pwm_csv_ready_ = true;
    }
    {
        constexpr int kSubPerCycle = 4;
        const double  sub_dt       = pwm_carrier_period_ / kSubPerCycle;
        const int     n_samples    = static_cast<int>(std::round(resolution_ / sub_dt));
        for (int k = 0; k < n_samples; ++k) {
            const double t   = sim_time_ + k * sub_dt;
            const double phi = std::fmod(t / pwm_carrier_period_, 1.0);
            const double tri = phi < 0.5 ? 2.0 * phi : 2.0 * (1.0 - phi);
            pwm_csv_ << std::format("{:.9f},{:.1f},{:.1f},{:.1f}\n", t, (duty_u > tri) ? vdc_ : 0.0,
                                    (duty_v > tri) ? vdc_ : 0.0, (duty_w > tri) ? vdc_ : 0.0);
        }
    }
    sim_time_ += resolution_;

    pre_angular_vel_      = angular_vel_;
    pre_diff_angular_vel_ = diff_angular_vel_;
    pre_mech_deg_         = mech_deg_;

    return {
        .phase_current   = phase_current,
        .electrical_deg  = elec_deg_,
        .electric_torque = elec_torque,
        .d_current       = d_current,
        .q_current       = q_current,
        .angular_vel     = angular_vel_,
        .mech_torque     = mech_torque,
        .mech_deg        = mech_deg_,
        .angle_error     = angle_error,
    };
}
