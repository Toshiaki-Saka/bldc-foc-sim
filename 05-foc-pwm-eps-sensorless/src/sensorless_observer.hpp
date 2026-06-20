#pragma once
// =============================================================================
//  sensorless_observer.hpp  —  センサーレス角度推定器 — 宣言
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 05-foc-pwm-eps-sensorless
//  誘起電圧オブザーバと PLL (位相同期ループ) によりロータの電気角・
//  角速度を推定するクラス SensorlessObserver を宣言する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include <Eigen/Dense>

// Sensorless rotor angle estimator for SPMSM.
//
// Algorithm:
//   1. Clarke transform: UVW -> ab (stationary alpha-beta frame)
//   2. Back-EMF estimate: ea = Va - R*ia - L*dia/dt
//                         eb = Vb - R*ib - L*dib/dt
//   3. First-order LPF on ea, eb
//   4. PLL drives theta_est so that ea*cos(theta_est) - eb*sin(theta_est) -> 0
//      (cross-product error ~= C*sin(theta - theta_est) for SPMSM back-EMF convention)
//
// Back-EMF convention in this codebase (derived from motor_vector_conv):
//   ea = (sqrt2/2)*Ke*omega*sin(theta)   ->  theta = atan2(ea, eb)
//   eb = (sqrt2/2)*Ke*omega*cos(theta)
//
// Startup handling:
//   The LPF introduces a phase lag phi = atan(omega_e / wc) that would appear
//   as a constant angle error in steady state.  get_angle_deg() compensates
//   this lag by adding +phi to theta_est.  During seeded startup the caller
//   force-syncs the estimator with the *true* electrical angle and electrical
//   speed, then blends from the true angle to the estimated angle over a short
//   window to avoid a step in the torque waveform.
class SensorlessObserver {
    double R_, L_, dt_;
    double ia_prev_, ib_prev_;   // alpha-beta current at previous step
    double ea_filt_, eb_filt_;   // filtered alpha-beta back-EMF
    double omega_est_;           // estimated electrical angular velocity [rad/s]
    double theta_est_;           // estimated electrical angle [rad]
    double lpf_alpha_;           // 1 - exp(-wc*dt)
    double lpf_cutoff_;          // LPF cutoff frequency wc [rad/s] (for phase compensation)
    double kp_, ki_;
    double err_i_;               // PLL error integral
    bool   initialized_;

public:
    struct Params {
        double R, L, dt;
        double lpf_cutoff;   // LPF cutoff frequency [rad/s]
        double kp, ki;       // PLL gains
    };

    void   init(const Params& p);
    // Call once per control step with the voltage applied in the *previous* step
    // and the current measured at the *current* step.
    void   update(const Eigen::Vector3d& voltage_uvw, const Eigen::Vector3d& current_uvw);

    // Force angle/speed during seeded startup so the BEMF filter warms up
    // while the PLL tracks the true state.  IMPORTANT: omega_elec must be the
    // *electrical* angular velocity [rad/s] (= mechanical speed * pole pairs).
    void   force_sync(double deg, double omega_elec);

    // Estimated electrical angle [deg].  The LPF phase lag is compensated using
    // the supplied electrical angular velocity so the steady-state angle error
    // stays small.  Pass the true (or best-known) electrical speed in rad/s.
    [[nodiscard]] double get_angle_deg(double omega_elec) const;

    // Raw (uncompensated) estimated angle [deg] -- mainly for diagnostics.
    [[nodiscard]] double get_raw_angle_deg() const;

    [[nodiscard]] double get_omega() const { return omega_est_; }
};
