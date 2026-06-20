// =============================================================================
//  motor_model.cpp  —  モータ電気・機械モデル (プラント) — 実装
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 01-foc-ideal-voltage
//  電気系は前進オイラー法、機械系は台形積分法で離散化し、印加電圧から
//  相電流・電磁トルク・回転速度・角度を 1 ステップ更新する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include "motor_model.hpp"
#include <cmath>
#include <format>
#include <numbers>

/*** MotorModel ***/

void MotorModel::init(const MotorConfig& cfg)
{
    inertia_            = cfg.inertia;
    coil_resistance_    = cfg.coil_resistance;
    counter_emf_        = cfg.counter_emf;
    torque_constant_    = cfg.torque_constant;
    viscous_resistance_ = cfg.viscous_resistance;
    inductance_         = cfg.inductance;
    resolution_         = cfg.resolution;
    pole_pairs_         = cfg.pole_pairs;

    load_torque_        = cfg.load_torque;
    csv_path_           = cfg.csv_path;
    mech_deg_           = cfg.initial_deg;
    elec_deg_           = cfg.initial_deg;
    pre_mech_deg_       = cfg.initial_deg;
}

MotorState MotorModel::update(const Eigen::Vector3d& input_voltage)
{
    if (!csv_ready_)
    {
        csv_.open(csv_path_);
        csv_ << "U,V,W,ElecDeg,Te,id,iq,omega,Tm,MechDeg,AngleError\n";
        csv_ready_ = true;
    }

    // UVW -> dq voltage
    const Eigen::Vector2d dq_voltage = MotorVectorConv::uvw_to_dq(input_voltage, elec_deg_);
    const double d_voltage = dq_voltage(0);
    const double q_voltage = dq_voltage(1);

    // Current dynamics (forward Euler)
    const double back_emf = counter_emf_ * angular_vel_;
    q_current_state_ += (q_voltage - back_emf - coil_resistance_ * q_current_state_) / inductance_ * resolution_;
    d_current_state_ += (d_voltage            - coil_resistance_ * d_current_state_) / inductance_ * resolution_;

    const double d_current = d_current_state_;
    const double q_current = q_current_state_;

    // Torques
    const double elec_torque = q_current * torque_constant_;
    const double mech_torque = elec_torque - load_torque_ - viscous_resistance_ * pre_angular_vel_;

    // Angular velocity (trapezoidal integration)
    diff_angular_vel_  = mech_torque / inertia_;
    angular_vel_      += (diff_angular_vel_ + pre_diff_angular_vel_) * resolution_ / 2.0;

    // Mechanical angle [deg]
    mech_deg_ += (angular_vel_ + pre_angular_vel_) * resolution_ * 0.5 * (180.0 / std::numbers::pi);
    mech_deg_  = std::fmod(mech_deg_, 360.0);
    if (mech_deg_ < 0.0) mech_deg_ += 360.0;

    // Electrical angle tracking with low-pass correction
    auto wrap360 = [](double v) {
        v = std::fmod(v, 360.0);
        return v < 0.0 ? v + 360.0 : v;
    };
    auto wrap_diff = [](double d) -> double {
        if (d >  180.0) return d - 360.0;
        if (d < -180.0) return d + 360.0;
        return d;
    };

    const double mech_step = wrap_diff(mech_deg_ - pre_mech_deg_);
    elec_deg_ += mech_step * pole_pairs_;

    const double target = wrap360(mech_deg_ * pole_pairs_);
    elec_deg_ += 0.05 * wrap_diff(target - elec_deg_);
    elec_deg_  = wrap360(elec_deg_);

    const double angle_error = wrap_diff(target - elec_deg_);

    // dq actual current -> UVW phase current (state variables, not voltage)
    const Eigen::Vector2d dq_current_actual { d_current_state_, q_current_state_ };
    const Eigen::Vector3d phase_current = MotorVectorConv::dq_to_uvw(dq_current_actual, elec_deg_);

    csv_ << std::format("{},{},{},{},{},{},{},{},{},{},{}\n",
        phase_current(0), phase_current(1), phase_current(2),
        elec_deg_, elec_torque, d_current, q_current,
        angular_vel_, mech_torque, mech_deg_, angle_error);

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
