#pragma once
// =============================================================================
//  eps_gearbox_model.hpp  —  EPS mechanism dynamics model — declarations
// -----------------------------------------------------------------------------
//  Project    : bldc-foc-sim / 05-foc-pwm-eps-sensorless
//  Declares the class representing the mechanical dynamics of the steering
//  column, torsion bar (spring-damper), reduction gear, and rack.
//
//  License    : Apache-2.0 (see LICENSE at repo root)
// =============================================================================

#include "sim_params.hpp"

// Physical parameters for the EPS gearbox mechanical model.
struct EpsGearboxConfig {
    double jsw;           // Steering wheel + upper column inertia [kg·m²]
    double jcol;          // Lower column base inertia (no motor/rack) [kg·m²]
    double jmotor;        // Motor rotor inertia [kg·m²]
    double rack_mass;     // Rack mass [kg]
    double ktb;           // Torsion bar stiffness [Nm/rad]
    double ctb;           // Torsion bar damping   [Nm·s/rad]
    double gear_ratio;    // Motor-to-column gear ratio (reduction gear)
    double pinion_radius; // Pinion radius [m]
    double spring_const;  // Rack spring load [N/m]  (spring load)
    double damping_const; // Rack viscous damping [N·s/m]
    double resolution;    // Simulation time step [s]
};

// All state variables output by one simulation step.
struct EpsGearboxState {
    double theta_sw;       // Steering wheel angle [rad]
    double omega_sw;       // Steering wheel angular velocity [rad/s]
    double theta_col;      // Lower column / pinion angle [rad]
    double omega_col;      // Lower column / pinion angular velocity [rad/s]
    double rack_disp;      // Rack displacement [m]  = pinion_radius * theta_col
    double rack_vel;       // Rack velocity [m/s]
    double rack_force;     // Spring + damper force on rack [N]
    double torsion_torque; // Torsion bar torque = torque sensor reading [Nm]
    double assist_torque;  // Assist torque delivered at pinion [Nm] = gear_ratio * Tm
};

// Two-mass EPS mechanical model:
//
//   Jsw * α_sw  = Th  − Ttb
//   Jcol_tot * α_col = Ttb + Ng*Tm − (Ks*rp²)*θcol − (Cs*rp²)*ωcol
//
// where Jcol_tot = jcol + jmotor*Ng² + rack_mass*rp²  (reflected inertias)
//       Ttb = ktb*(θsw−θcol) + ctb*(ωsw−ωcol)        (torsion bar / sensor torque)
//       rack_disp = rp*θcol,   rack_force = Ks*rack_disp + Cs*rack_vel
//
class EpsGearboxModel {
    double jsw_      = 0.04;
    double jcol_tot_ = 0.003;
    double ktb_      = 143.24;
    double ctb_      = 0.1;
    double ng_       = 2.714;
    double rp_       = 0.008;
    double ks_       = 80000.0;
    double cs_       = 500.0;
    double dt_       = kResolution;

    double theta_sw_  = 0.0;
    double omega_sw_  = 0.0;
    double theta_col_ = 0.0;
    double omega_col_ = 0.0;

public:
    EpsGearboxModel() = default;
    explicit EpsGearboxModel(const EpsGearboxConfig& cfg) { init(cfg); }

    void init(const EpsGearboxConfig& cfg);

    // Advance one time step.
    // hand_torque  : driver steering torque Th [Nm]
    // motor_torque : motor shaft torque Tm [Nm]
    [[nodiscard]] EpsGearboxState update(double hand_torque, double motor_torque);
};
