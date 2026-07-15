#pragma once
// =============================================================================
//  motor_model.hpp  —  motor electrical and mechanical model (plant) — declarations
// -----------------------------------------------------------------------------
//  Project : bldc-foc-sim / 01-foc-ideal-voltage
//  Declares the MotorModel class, which represents the state equations of the
//  electrical subsystem (dq-axis currents) and mechanical subsystem (rotational
//  speed and angle) of a three-phase BLDC motor.
//
//  License : MIT (see LICENSE at repo root)
// =============================================================================

#include <fstream>
#include <numbers>
#include <string>
#include <Eigen/Dense>
#include "motor_vector_conv.hpp"

struct MotorConfig {
    double inertia;
    double coil_resistance;
    double counter_emf;
    double torque_constant;
    double viscous_resistance;
    double inductance;
    double resolution;
    double initial_deg = 0.0;
    double load_torque = 0.0;
    double pole_pairs  = 1.0;

    std::string csv_path = "data/sim_output.csv";
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

    double mech_deg_     = 0.0;
    double elec_deg_     = 0.0;
    double pre_mech_deg_ = 0.0;

    double pole_pairs_ = 1.0;

    double load_torque_ = 0.0;

    double q_current_state_ = 0.0;
    double d_current_state_ = 0.0;

    std::string   csv_path_ = "data/sim_output.csv";
    std::ofstream csv_;
    bool          csv_ready_ = false;

public:
    MotorModel() = default;
    explicit MotorModel(const MotorConfig& cfg) { init(cfg); }

    void                     init(const MotorConfig& cfg);
    [[nodiscard]] MotorState update(const Eigen::Vector3d& input_voltage);
};
