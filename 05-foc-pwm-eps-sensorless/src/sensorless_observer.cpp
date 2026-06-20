// =============================================================================
//  sensorless_observer.cpp  —  センサーレス角度推定器 — 実装
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 05-foc-pwm-eps-sensorless
//  αβ 座標系で誘起電圧を推定し、LPF で平滑化したのち PLL で角度・速度に
//  ロックする。LPF の位相遅れは get_angle_deg() で補償する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include "sensorless_observer.hpp"
#include "motor_vector_conv.hpp"
#include <cmath>
#include <numbers>

void SensorlessObserver::init(const Params& p)
{
    R_ = p.R;  L_ = p.L;  dt_ = p.dt;
    lpf_cutoff_  = p.lpf_cutoff;
    lpf_alpha_   = 1.0 - std::exp(-p.lpf_cutoff * p.dt);
    kp_          = p.kp;
    ki_          = p.ki;
    ia_prev_     = 0.0;
    ib_prev_     = 0.0;
    ea_filt_     = 0.0;
    eb_filt_     = 0.0;
    omega_est_   = 0.0;
    theta_est_   = 0.0;
    err_i_       = 0.0;
    initialized_ = false;
}

void SensorlessObserver::update(const Eigen::Vector3d& voltage_uvw,
                                 const Eigen::Vector3d& current_uvw)
{
    const Eigen::Vector2d vab = MotorVectorConv::uvw_to_alphabeta(voltage_uvw);
    const Eigen::Vector2d iab = MotorVectorConv::uvw_to_alphabeta(current_uvw);
    const double va = vab(0), vb = vab(1);
    const double ia = iab(0), ib = iab(1);

    if (!initialized_) {
        ia_prev_     = ia;
        ib_prev_     = ib;
        initialized_ = true;
        return;
    }

    // Back-EMF estimate: ea = Va(k-1) - R*ia(k-1) - L*(ia(k) - ia(k-1))/dt
    // Must use ia_prev_ (old current) in the R term because the applied voltage va
    // corresponds to the previous step when ia_prev_ was the instantaneous current.
    const double ea = va - R_ * ia_prev_ - L_ * (ia - ia_prev_) / dt_;
    const double eb = vb - R_ * ib_prev_ - L_ * (ib - ib_prev_) / dt_;

    // Low-pass filter
    ea_filt_ += (ea - ea_filt_) * lpf_alpha_;
    eb_filt_ += (eb - eb_filt_) * lpf_alpha_;

    // PLL: cross-product error ~= C*sin(theta_true - theta_est)
    //   With ea = C*sin(theta), eb = C*cos(theta):
    //   err = ea*cos(theta_est) - eb*sin(theta_est) = C*sin(theta - theta_est)
    const double err = ea_filt_ * std::cos(theta_est_) - eb_filt_ * std::sin(theta_est_);
    err_i_     += err * dt_;
    omega_est_  = kp_ * err + ki_ * err_i_;
    theta_est_ += omega_est_ * dt_;

    // Wrap to [0, 2pi)
    theta_est_ = std::fmod(theta_est_, 2.0 * std::numbers::pi);
    if (theta_est_ < 0.0) theta_est_ += 2.0 * std::numbers::pi;

    ia_prev_ = ia;
    ib_prev_ = ib;
}

void SensorlessObserver::force_sync(double deg, double omega_elec)
{
    // omega_elec is the ELECTRICAL angular velocity [rad/s].
    // The PLL integrates the electrical angle, so the integral term must be
    // seeded with the electrical speed (not the mechanical speed).
    theta_est_ = deg * std::numbers::pi / 180.0;
    omega_est_ = omega_elec;
    err_i_     = (ki_ > 0.0) ? omega_elec / ki_ : 0.0;
}

double SensorlessObserver::get_angle_deg(double omega_elec) const
{
    // Compensate the LPF phase lag.  A first-order LPF with cutoff wc delays a
    // signal of electrical angular frequency omega_e by phi = atan(omega_e/wc).
    // The back-EMF (and therefore the PLL input) is delayed by this amount, so
    // the estimated angle lags the true angle by phi in steady state.  Adding
    // +phi back removes the bulk of the constant angle error.
    //
    // omega_elec is supplied by the caller (it knows the true electrical speed
    // during seeded startup and a reliable estimate afterwards), which is more
    // robust than relying on the PLL's internal omega during transients.
    double phi = 0.0;
    if (lpf_cutoff_ > 0.0)
        phi = std::atan2(omega_elec, lpf_cutoff_);

    double comp = theta_est_ + phi;
    comp = std::fmod(comp, 2.0 * std::numbers::pi);
    if (comp < 0.0) comp += 2.0 * std::numbers::pi;
    return comp * 180.0 / std::numbers::pi;
}

double SensorlessObserver::get_raw_angle_deg() const
{
    return theta_est_ * 180.0 / std::numbers::pi;
}
