// =============================================================================
//  main.cpp  —  シミュレーションのエントリポイント
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 01-foc-ideal-voltage
//  コマンドライン引数を解析し、モータモデルと FOC コントローラを構成して
//  時間ステップごとのシミュレーションループを実行する。
//  結果は RESULT 行 (標準出力) と CSV ファイルに出力される。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include "motor_controller.hpp"
#include "motor_model.hpp"
#include "csv_verifier.hpp"
#include "sim_params.hpp"

static void print_tn_characteristics(double kt, double ke, double resistance, double viscous,
                                     double iq_target, double load_torque, double omega_sim) {
    const double te_rated   = kt * iq_target;
    const double omega_free = te_rated / viscous;

    std::printf("\n=== T-n Characteristics (FOC, iq* = %.1f A) ===\n", iq_target);
    std::printf("  Motor Kt = %.6f Nm/A,  Ke = %.6f V/(rad/s)\n", kt, ke);
    std::printf("  R = %.4f Ohm,  B = %.6f Nm/(rad/s)\n", resistance, viscous);
    std::printf("  Rated torque Te = %.4f Nm,  No-load speed = %.2f rad/s\n", te_rated, omega_free);
    std::printf("\n");
    std::printf("  %-18s  %-15s  %-6s\n", "Load Torque [Nm]", "omega_ss [rad/s]", "");
    std::printf("  %-18s  %-15s\n", "------------------", "---------------");

    const double omega_op_analytic = (te_rated - load_torque) / viscous;

    constexpr int kPoints  = 11;
    bool          inserted = false;
    double        prev_tl  = -1.0;
    for (int i = 0; i < kPoints; ++i) {
        const double tl    = te_rated * i / (kPoints - 1);
        const double omega = (te_rated - tl) / viscous;

        if (!inserted && prev_tl < load_torque && load_torque < tl) {
            std::printf("  %18.4f  %15.2f  <- sim: %.2f rad/s\n", load_torque, omega_op_analytic,
                        omega_sim);
            inserted = true;
        }
        std::printf("  %18.4f  %15.2f\n", tl, omega);
        prev_tl = tl;
    }
    if (!inserted) {
        std::printf("  %18.4f  %15.2f  <- sim: %.2f rad/s\n", load_torque, omega_op_analytic,
                    omega_sim);
    }
}

int main(int argc, char* argv[]) {
    // Motor / plant parameters (default from sim_params.hpp, overridable via CLI)
    double kt         = kKt;
    double ke         = kKe;
    double resistance = kR;
    double inductance = kL;
    double viscous    = kB;
    double inertia    = kJ;
    double pole_pairs = kPolePairs;
    double wn         = kWn;
    double zeta       = kZeta;

    // Simulation conditions (overridable via CLI)
    double      iq_ref       = kDefaultIqRef;
    double      iq_step_time = -1.0;
    double      iq_step_val  = 0.0;
    double      tload        = kDefaultTload;
    double      span         = kCalcSpan;
    bool        no_csv       = false;
    bool        quiet        = false;
    bool        midpoint     = true;
    bool        decoupling   = true;
    std::string csv_out      = "data/sim_output.csv";

    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--kt") == 0 && i + 1 < argc)
            kt = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--ke") == 0 && i + 1 < argc)
            ke = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--r") == 0 && i + 1 < argc)
            resistance = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--l") == 0 && i + 1 < argc)
            inductance = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--b") == 0 && i + 1 < argc)
            viscous = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--j") == 0 && i + 1 < argc)
            inertia = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--pole_pairs") == 0 && i + 1 < argc)
            pole_pairs = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--wn") == 0 && i + 1 < argc)
            wn = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--zeta") == 0 && i + 1 < argc)
            zeta = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--iq_ref") == 0 && i + 1 < argc)
            iq_ref = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--tload") == 0 && i + 1 < argc)
            tload = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--span") == 0 && i + 1 < argc)
            span = std::atof(argv[++i]);
        else if (std::strcmp(argv[i], "--csv_out") == 0 && i + 1 < argc)
            csv_out = argv[++i];
        else if (std::strcmp(argv[i], "--no_csv") == 0)
            no_csv = true;
        else if (std::strcmp(argv[i], "--quiet") == 0)
            quiet = true;
        else if (std::strcmp(argv[i], "--midpoint") == 0)
            midpoint = true;
        else if (std::strcmp(argv[i], "--no-midpoint") == 0)
            midpoint = false;
        else if (std::strcmp(argv[i], "--decoupling") == 0)
            decoupling = true;
        else if (std::strcmp(argv[i], "--no-decoupling") == 0)
            decoupling = false;
        else if (std::strcmp(argv[i], "--iq_step") == 0 && i + 2 < argc) {
            iq_step_time = std::atof(argv[++i]);
            iq_step_val  = std::atof(argv[++i]);
        }
    }

    const int kSteps = static_cast<int>(span / kResolution);

    MotorModel model{MotorConfig{
        .inertia            = inertia,
        .coil_resistance    = resistance,
        .counter_emf        = ke,
        .torque_constant    = kt,
        .viscous_resistance = viscous,
        .inductance         = inductance,
        .resolution         = kResolution,
        .initial_deg        = 0.0,
        .load_torque        = tload,
        .csv_path           = no_csv ? "NUL" : csv_out,
    }};

    // 2nd-order pole placement: Kp = 2ζωnL − R, Ki = ωn²L
    const double kKp = 2.0 * zeta * wn * inductance - resistance;
    const double kKi = wn * wn * inductance;

    MotorController controller;
    controller.init(Axis::D, {.kp = kKp, .ki = kKi, .target_current = 0.0, .max_current = 100.0},
                    kResolution);
    controller.init(Axis::Q, {.kp = kKp, .ki = kKi, .target_current = iq_ref, .max_current = 100.0},
                    kResolution);
    controller.set_options(midpoint, decoupling);

    Eigen::Vector3d current = Eigen::Vector3d::Zero();
    double          deg     = 0.0;
    MotorState      last_state{};

    double omega_e    = 0.0; // electrical angular velocity [rad/s]
    bool   iq_stepped = false;
    for (int step = 0; step < kSteps; ++step) {
        // Apply the q-axis reference step once the configured time is reached.
        if (iq_step_time >= 0.0 && !iq_stepped && step * kResolution >= iq_step_time) {
            controller.set_target_q(iq_step_val);
            iq_stepped = true;
        }
        const auto ctrl = controller.compute(current, deg, omega_e);
        last_state      = model.update(ctrl.phase_signal);

        current = last_state.phase_current;
        deg     = last_state.electrical_deg;
        omega_e = last_state.angular_vel * pole_pairs;
    }

    // Machine-parseable result line (always printed)
    const double iq_ss = last_state.q_current;
    const double id_ss = last_state.d_current;
    std::printf("RESULT omega_ss=%.6f iq_ss=%.6f id_ss=%.6f tload=%.6f te_ss=%.6f\n",
                last_state.angular_vel, iq_ss, id_ss, tload, last_state.electric_torque);

    if (!quiet) {
        std::printf("Simulation complete (%d steps, span=%.3fs).\n", kSteps, span);
        std::printf("  Midpoint  : %s\n", midpoint ? "ON" : "OFF");
        std::printf("  Decoupling: %s\n", decoupling ? "ON" : "OFF");
        if (!no_csv)
            std::printf("  Output    : %s\n", csv_out.c_str());

        print_tn_characteristics(kt, ke, resistance, viscous, iq_ref, tload,
                                 last_state.angular_vel);

        if (!no_csv) {
            const auto result =
                verify_csv("data/motor_log.csv", csv_out.c_str(), "data/verification.csv");

            if (!result.ref_available) {
                std::printf(
                    "\n  Reference : data/motor_log.csv not found - skipping verification.\n");
            } else {
                std::printf("\n  Reference : data/motor_log.csv\n");
                std::printf("  Diff      : data/verification.csv\n\n");
                std::printf("%-12s  %15s  %15s\n", "Column", "MaxAbsError", "MeanAbsError");
                std::printf("%-12s  %15s  %15s\n", "------", "-----------", "------------");
                for (const auto& col : result.columns)
                    std::printf("%-12s  %15.6e  %15.6e\n", col.name.c_str(), col.max_abs_error,
                                col.mean_abs_error);
                std::printf("\nRows compared: %d\n", result.total_rows);
            }
        }
    }

    return 0;
}
