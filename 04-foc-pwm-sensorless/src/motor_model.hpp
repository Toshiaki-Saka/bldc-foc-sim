#pragma once
// =============================================================================
//  motor_model.hpp  —  モータ電気・機械モデル (プラント) — 宣言
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 04-foc-pwm-sensorless
//  三相 BLDC モータの電気系 (dq 軸電流) と機械系 (回転速度・角度) の
//  状態方程式を表現するクラス MotorModel を宣言する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include <fstream>
#include <numbers>
#include <string>
#include <Eigen/Dense>
#include "motor_vector_conv.hpp"
#include "sim_params.hpp"

struct MotorConfig {
    double inertia;
    double coil_resistance;
    double counter_emf;
    double torque_constant;
    double viscous_resistance;
    double inductance;
    double resolution;
    double initial_deg        = 0.0;
    double load_torque        = 0.0;
    double pole_pairs         = 1.0;
    double vdc                = kVdc;
    double pwm_carrier_period = kPwmCarrierPeriod;

    std::string csv_path     = "data/sim_output.csv";
    std::string pwm_csv_path = "data/pwm_waveform.csv";
};

struct MotorState {
    Eigen::Vector3d phase_current;
    double          electrical_deg;
    double          electric_torque;
    double          d_current;
    double          q_current;
    double          angular_vel;
    double          mech_torque;
    double          mech_deg;
    double          angle_error;
};

class MotorModel {
    double angular_vel_          = 0.0;
    double pre_angular_vel_      = 0.0;
    double diff_angular_vel_     = 0.0;
    double pre_diff_angular_vel_ = 0.0;

    double resolution_         = 0.000250;
    double inertia_            = 0.000053;
    double coil_resistance_    = 0.015;
    double counter_emf_        = 0.0412;
    double torque_constant_    = 0.0412;
    double viscous_resistance_ = 1.0e-2 / (2.0 * std::numbers::pi);
    double inductance_         = 0.01;

    double mech_deg_ = 0.0;
    double elec_deg_ = 0.0;

    double pole_pairs_ = 1.0;

    double load_torque_ = 0.0;
    double vdc_         = kVdc;

    double q_current_state_ = 0.0;
    double d_current_state_ = 0.0;

    std::string   csv_path_ = "data/sim_output.csv";
    std::ofstream csv_;
    bool          csv_ready_ = false;

    std::string   pwm_csv_path_ = "data/pwm_waveform.csv";
    std::ofstream pwm_csv_;
    bool          pwm_csv_ready_      = false;
    double        pwm_carrier_period_ = kPwmCarrierPeriod;
    double        sim_time_           = 0.0;

public:
    MotorModel() = default;
    explicit MotorModel(const MotorConfig& cfg) { init(cfg); }

    void init(const MotorConfig& cfg);
    // estimated_deg: sensorless angle estimate [deg] - logged for error analysis
    [[nodiscard]] MotorState update(const Eigen::Vector3d& input_voltage,
                                    double                 estimated_deg = 0.0);
};
