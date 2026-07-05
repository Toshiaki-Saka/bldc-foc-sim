// =============================================================================
//  motor_controller.cpp  —  FOC コントローラ・PI 制御器 — 実装
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 02-foc-pwm-drive
//  測定電流を dq 軸に変換し、PI 制御で電圧指令を算出する。
//  オプションで非干渉制御のフィードフォワード項と中点変調を適用する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include "motor_controller.hpp"
#include <algorithm>
#include <cmath>
#include <numbers>

/*** PidController ***/

void PidController::init(const PidConfig& cfg) {
    kp_          = cfg.kp;
    ki_          = cfg.ki;
    kd_          = cfg.kd;
    output_max_  = cfg.output_max;
    resolution_  = cfg.resolution;
    initialized_ = false;
}

void PidController::update(double measurement, double setpoint) {
    dev_p_ = setpoint - measurement;

    if (!initialized_) {
        dev_d_       = 0.0;
        dev_i_       = 0.0;
        prev_dev_p_  = dev_p_;
        initialized_ = true;
    } else {
        dev_i_ += (dev_p_ + prev_dev_p_) * resolution_ / 2.0; // trapezoidal integration
        dev_d_      = dev_p_ - prev_dev_p_;
        prev_dev_p_ = dev_p_;
    }
}

double PidController::output() const {
    return std::clamp(kp_ * dev_p_ + ki_ * dev_i_ + kd_ * dev_d_, -output_max_, output_max_);
}

/*** MotorController ***/

void MotorController::init(Axis axis, const AxisConfig& cfg, double resolution) {
    const PidConfig pid_cfg{
        .kp         = cfg.kp,
        .ki         = cfg.ki,
        .kd         = cfg.kd,
        .output_max = cfg.max_current,
        .resolution = resolution,
    };

    if (axis == Axis::D) {
        target_d_ = cfg.target_current;
        pid_d_.init(pid_cfg);
    } else {
        target_q_ = cfg.target_current;
        pid_q_.init(pid_cfg);
    }
}

ControlOutput MotorController::compute(const Eigen::Vector3d& current, double deg,
                                       double omega_elec) {
    const Eigen::Vector2d dq_current = MotorVectorConv::uvw_to_dq(current, deg);
    const double          id         = dq_current(0);
    const double          iq         = dq_current(1);

    pid_d_.update(id, target_d_);
    pid_q_.update(iq, target_q_);

    Eigen::Vector2d dq_cmd{pid_d_.output(), pid_q_.output()};

    // --- dq-axis decoupling (non-interacting control) [optional] ----------
    //  The dq voltage equations contain cross-coupling terms:
    //    vd = R*id + L*did/dt - omega_e*L*iq
    //    vq = R*iq + L*diq/dt + omega_e*L*id + Ke*omega_m
    //  Adding the boxed terms as feed-forward cancels the cross-coupling so
    //  that the d and q axes behave as independent first-order systems.
    if (use_decoupling_) {
        const double vd_ff = -omega_elec * kL * iq;
        const double vq_ff = omega_elec * kL * id + kKe * (omega_elec / kPolePairs);
        dq_cmd(0) += vd_ff;
        dq_cmd(1) += vq_ff;
    }

    // PWM duty and peak voltage derived from q-axis current reference:
    //   125 A -> 95 % duty, linear mapping clamped to [0, kPwmMaxDuty].
    //  With mid-point modulation the usable peak phase voltage is extended by
    //  2/sqrt(3); without it the classic Vdc/2 sine limit applies.
    const double duty   = std::clamp(std::abs(target_q_) / kPwmMaxAmp, 0.0, 1.0) * kPwmMaxDuty;
    const double boost  = use_midpoint_ ? (2.0 / std::numbers::sqrt3) : 1.0;
    const double v_peak = duty * vdc_ / 2.0 * boost;    // peak phase-to-neutral voltage [V]
    const double v_rms  = v_peak / std::numbers::sqrt2; // RMS phase voltage [V]

    // Clamp dq voltage vector magnitude to PWM-derived peak voltage limit
    const double mag = dq_cmd.norm();
    if (mag > v_peak)
        dq_cmd *= (v_peak / mag);

    Eigen::Vector3d phase = MotorVectorConv::dq_to_uvw(dq_cmd, deg);

    // --- mid-point (zero-sequence) modulation [optional] ------------------
    if (use_midpoint_)
        phase = MotorVectorConv::apply_midpoint_modulation(phase);

    return {.phase_signal = phase, .pwm_duty = duty, .v_rms = v_rms};
}
