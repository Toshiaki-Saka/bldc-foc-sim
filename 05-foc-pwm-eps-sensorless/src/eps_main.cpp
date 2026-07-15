// =============================================================================
//  eps_main.cpp  —  Entry point for the integrated EPS simulation
// -----------------------------------------------------------------------------
//  Project    : bldc-foc-sim / 05-foc-pwm-eps-sensorless
//  Couples the EPS mechanism (column, torsion bar, reduction gear, rack) with
//  the BLDC motor and FOC controller to reproduce the assist behavior in
//  response to driver steering.
//
//  License    : MIT (see LICENSE at repo root)
// =============================================================================

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <format>
#include <fstream>
#include <numbers>
#include <string>

#include "eps_controller.hpp"
#include "eps_gearbox_model.hpp"
#include "eps_sim_params.hpp"
#include "motor_controller.hpp"
#include "motor_model.hpp"
#include "sim_params.hpp"

int main(int argc, char* argv[]) {
    double      span       = kEpsCalcSpan;
    double      torque_max = kEpsHandTorqueMax;
    double      ramp_dur   = kEpsRampDuration;
    bool        no_csv     = false;
    bool        quiet      = false;
    bool        midpoint   = false;
    bool        decoupling = false;
    std::string csv_out    = "data/eps_output.csv";

    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--span") == 0 && i + 1 < argc)
            span = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--tmax") == 0 && i + 1 < argc)
            torque_max = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--ramp") == 0 && i + 1 < argc)
            ramp_dur = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--csv_out") == 0 && i + 1 < argc)
            csv_out = argv[++i];
        else if (std::strcmp(argv[i], "--no_csv") == 0)
            no_csv = true;
        else if (std::strcmp(argv[i], "--quiet") == 0)
            quiet = true;
        else if (std::strcmp(argv[i], "--midpoint") == 0)
            midpoint = true;
        else if (std::strcmp(argv[i], "--decoupling") == 0)
            decoupling = true;
    }

    const double ng = kEpsGearRatio;

    // --- EPS mechanical system (steering wheel + torsion bar + column + pinion + rack + spring)
    // ---
    EpsGearboxModel gearbox{EpsGearboxConfig{
        .jsw           = kJsw,
        .jcol          = kJcolBase,
        .jmotor        = kJ,
        .rack_mass     = kRackMass,
        .ktb           = kTorsionBarStiffness,
        .ctb           = kTorsionBarDamping,
        .gear_ratio    = ng,
        .pinion_radius = kPinionRadius,
        .spring_const  = kRackSpringConst,
        .damping_const = kRackDampingConst,
        .resolution    = kResolution,
    }};

    // --- EPS assist controller (V-curve assist map: torsion torque → iq_ref) ---
    EpsController eps_ctrl{EpsControllerConfig{
        .deadzone = kEpsDeadzone,
        .gain     = kEpsAssistGain,
        .iq_max   = kEpsIqMax,
    }};

    // --- BLDC motor electrical model (dq current dynamics + torque generation) ---
    MotorModel motor{MotorConfig{
        .inertia            = kJ,
        .coil_resistance    = kR,
        .counter_emf        = kKe,
        .torque_constant    = kKt,
        .viscous_resistance = kB,
        .inductance         = kL,
        .resolution         = kResolution,
        .load_torque        = 0.0, // mechanical coupling handled by EpsGearboxModel
        .vdc                = kVdc,
        .csv_path           = "NUL", // motor-internal CSV suppressed; combined CSV output below
        .pwm_csv_path       = "NUL",
    }};

    // --- FOC current controller (d/q axis PI) ---
    // 2nd-order pole placement: Kp = 2ζωnL − R, Ki = ωn²L
    const double    kKp = 2.0 * kZeta * kWn * kL - kR;
    const double    kKi = kWn * kWn * kL;
    MotorController foc;
    foc.init(Axis::D, {.kp = kKp, .ki = kKi, .target_current = 0.0, .max_current = 120.0},
             kResolution);
    foc.init(Axis::Q, {.kp = kKp, .ki = kKi, .target_current = 0.0, .max_current = 120.0},
             kResolution);
    foc.set_vdc(kVdc);
    foc.set_options(midpoint, decoupling);

    // Open combined output CSV
    std::ofstream csv;
    if (!no_csv) {
        csv.open(csv_out);
        if (csv.is_open()) {
            csv << "time,hand_torque,torsion_torque,sensor_filt,iq_ref,iq_actual,"
                   "motor_torque,assist_torque,theta_sw,theta_col,"
                   "omega_sw,omega_col,rack_disp,rack_vel,rack_force,"
                   "omega_motor,d_current,mech_deg\n";
        }
    }

    double          sensor_filt = 0.0;
    EpsGearboxState gearbox_state{};
    MotorState      motor_state{};
    double          last_iq_ref   = 0.0;
    Eigen::Vector3d motor_current = Eigen::Vector3d::Zero();
    double          motor_deg     = 0.0;

    const int kSteps = static_cast<int>(span / kResolution);

    for (int step = 0; step < kSteps; ++step) {
        const double t = step * kResolution;

        // Driver hand torque ramp: 0 → torque_max in ramp_dur seconds, then hold
        const double hand_torque = torque_max * std::min(t / ramp_dur, 1.0);

        // ECU torque sensor LPF (prevents exciting mechanical resonance at ~9.5 Hz)
        sensor_filt +=
            (gearbox_state.torsion_torque - sensor_filt) * kEpsSensorLpfOmega * kResolution;

        // EPS ECU: V-curve assist map → q-axis current reference
        const double iq_ref = eps_ctrl.compute_iq_ref(sensor_filt);
        last_iq_ref         = iq_ref;

        // FOC: update q-axis target then compute 3-phase voltage commands
        foc.set_target_q(iq_ref);
        const double motor_omega_elec = motor_state.angular_vel * kPolePairs;
        const auto   ctrl             = foc.compute(motor_current, motor_deg, motor_omega_elec);

        // Kinematic constraint: motor shaft speed = gear_ratio × column speed
        // This enforces the rigid coupling through the gearbox and gives correct back-EMF.
        motor.set_angular_vel(kEpsGearRatio * gearbox_state.omega_col);

        // Motor electrical model: 3-phase BLDC dynamics → electromagnetic torque
        motor_state = motor.update(ctrl.phase_signal);

        // EPS mechanical model: motor torque × Ng → pinion torque → rack force
        gearbox_state = gearbox.update(hand_torque, motor_state.electric_torque);

        // Feed back motor state to FOC for next step
        motor_current = motor_state.phase_current;
        motor_deg     = motor_state.electrical_deg;

        if (csv.is_open()) {
            csv << std::format(
                "{:.6f},{:.6f},{:.6f},{:.6f},{:.6f},{:.6f},"
                "{:.6f},{:.6f},{:.6f},{:.6f},"
                "{:.6f},{:.6f},{:.9f},{:.6f},{:.4f},"
                "{:.6f},{:.6f},{:.4f}\n",
                t, hand_torque, gearbox_state.torsion_torque, sensor_filt, iq_ref,
                motor_state.q_current, motor_state.electric_torque, gearbox_state.assist_torque,
                gearbox_state.theta_sw, gearbox_state.theta_col, gearbox_state.omega_sw,
                gearbox_state.omega_col, gearbox_state.rack_disp, gearbox_state.rack_vel,
                gearbox_state.rack_force, motor_state.angular_vel, motor_state.d_current,
                motor_state.mech_deg);
        }
    }

    // Machine-parseable result line (used by eps_vcurve_sweep.py)
    std::printf("RESULT torsion_ss=%.6f assist_ss=%.6f rack_force_ss=%.2f"
                " rack_disp_mm=%.3f iq_ref_ss=%.4f\n",
                gearbox_state.torsion_torque, gearbox_state.assist_torque, gearbox_state.rack_force,
                gearbox_state.rack_disp * 1000.0, last_iq_ref);

    if (!quiet) {
        const double max_assist = ng * kKt * kEpsIqMax;
        std::printf("\n=== EPS integrated model simulation ===\n");
        std::printf("  Configuration: BLDC motor (FOC) + reduction gear + pinion/rack + spring "
                    "load\n");
        std::printf("\n  --- Parameters ---\n");
        std::printf("  Gear ratio Ng                : %.4f\n", ng);
        std::printf("  Motor Kt                     : %.6f Nm/A\n", kKt);
        std::printf("  Max assist torque (pinion)   : %.3f Nm  (Ng × Kt × Iq_max)\n", max_assist);
        std::printf("  Torsion bar stiffness        : %.2f Nm/rad\n", kTorsionBarStiffness);
        std::printf("  Rack spring constant         : %.0f N/m\n", kRackSpringConst);
        std::printf("  Pinion radius                : %.1f mm\n", kPinionRadius * 1000.0);
        std::printf("  Assist gain                  : %.1f A/Nm  (dead zone: %.2f Nm)\n",
                    kEpsAssistGain, kEpsDeadzone);
        std::printf("\n  --- Steady state (t = %.2f s,  Th = %.2f Nm) ---\n", span, torque_max);
        std::printf("  Torque sensor reading        : %.4f Nm\n", gearbox_state.torsion_torque);
        std::printf("  Iq command                   : %.2f A\n", last_iq_ref);
        std::printf("  Iq actual (q current)        : %.2f A\n", motor_state.q_current);
        std::printf("  Assist torque (pinion)       : %.4f Nm\n", gearbox_state.assist_torque);
        std::printf("  Rack force                   : %.2f N\n", gearbox_state.rack_force);
        std::printf("  Rack displacement            : %.2f mm\n", gearbox_state.rack_disp * 1000.0);
        std::printf("  Motor angular velocity       : %.2f rad/s\n", motor_state.angular_vel);
        if (!no_csv)
            std::printf("  Output CSV                   : %s\n", csv_out.c_str());
    }

    return 0;
}
