// =============================================================================
//  test_vector_conv.cpp  —  numerical unit tests for the coordinate transforms
// -----------------------------------------------------------------------------
//  Project : bldc-foc-sim  (shared test across all models)
//  Verifies the invertibility, zero-sequence component, and known values of the
//  Clarke / Park transforms, and that midpoint modulation preserves the
//  line-to-line voltage. A lightweight harness with no external test-framework
//  dependency.
//
//  Compiled from each model's CMakeLists together with that model's own
//  motor_vector_conv.cpp. Since it is a shared source, a single description
//  guarantees that every model's transform implementation satisfies the same
//  invariants (this also serves as drift detection).
//
//  License : MIT (see LICENSE at repo root)
// =============================================================================

#include <cmath>
#include <cstdio>

#include <Eigen/Dense>

#include "motor_vector_conv.hpp"

namespace {

int g_failures = 0;
int g_checks   = 0;

// Checks that |a - b| <= tol. On failure, prints the file/line and values.
void check_close(double a, double b, double tol, const char* what, int line) {
    ++g_checks;
    if (std::abs(a - b) > tol || std::isnan(a) || std::isnan(b)) {
        ++g_failures;
        std::printf("  [FAIL] line %d: %s  (got %.10g, expected %.10g, tol %.1e)\n", line, what, a,
                    b, tol);
    }
}

#define CHECK_CLOSE(a, b, tol) check_close((a), (b), (tol), #a " == " #b, __LINE__)

constexpr double kTol = 1e-9;

// The forward-inverse Park/Clarke transform is the identity map (with the
// amplitude-invariant form, dq->uvw->dq is fully recovered).
void test_dq_roundtrip() {
    std::printf("test_dq_roundtrip\n");
    const double          angles[] = {0.0, 30.0, 90.0, 137.5, 250.0, 359.0, -45.0};
    const Eigen::Vector2d dqs[] = {{0.0, 0.0}, {1.0, 0.0}, {0.0, 1.0}, {12.3, -4.5}, {-7.0, 8.0}};
    for (double deg : angles) {
        for (const auto& dq : dqs) {
            const Eigen::Vector3d uvw  = MotorVectorConv::dq_to_uvw(dq, deg);
            const Eigen::Vector2d back = MotorVectorConv::uvw_to_dq(uvw, deg);
            CHECK_CLOSE(back.x(), dq.x(), kTol);
            CHECK_CLOSE(back.y(), dq.y(), kTol);
        }
    }
}

// The output of dq_to_uvw contains no zero-sequence component (the three phases sum to zero).
void test_zero_sequence_free() {
    std::printf("test_zero_sequence_free\n");
    const Eigen::Vector3d uvw = MotorVectorConv::dq_to_uvw({5.0, -3.0}, 42.0);
    CHECK_CLOSE(uvw.sum(), 0.0, kTol);
}

// Concrete value for a known input: dq=(1,0), θ=0 → uvw = √2·(1, -0.5, -0.5).
void test_known_value() {
    std::printf("test_known_value\n");
    const Eigen::Vector3d uvw = MotorVectorConv::dq_to_uvw({1.0, 0.0}, 0.0);
    const double          s   = std::sqrt(2.0);
    CHECK_CLOSE(uvw(0), s * 1.0, kTol);
    CHECK_CLOSE(uvw(1), s * -0.5, kTol);
    CHECK_CLOSE(uvw(2), s * -0.5, kTol);
}

// Midpoint modulation only adds a common-mode component, so the line-to-line voltage is unchanged.
void test_midpoint_preserves_line_voltage() {
    std::printf("test_midpoint_preserves_line_voltage\n");
    const Eigen::Vector3d in[] = {{10.0, -3.0, -7.0}, {1.0, 1.0, 1.0}, {-4.0, 9.0, 2.5}};
    for (const auto& uvw : in) {
        const Eigen::Vector3d out = MotorVectorConv::apply_midpoint_modulation(uvw);
        CHECK_CLOSE(out(0) - out(1), uvw(0) - uvw(1), kTol);
        CHECK_CLOSE(out(1) - out(2), uvw(1) - uvw(2), kTol);
        CHECK_CLOSE(out(2) - out(0), uvw(2) - uvw(0), kTol);
        // After modulation, the max and min are symmetric about the origin (midpoint is 0).
        CHECK_CLOSE(out.maxCoeff() + out.minCoeff(), 0.0, kTol);
    }
}

} // namespace

int main() {
    std::printf("== bldc-foc-sim vector-conv unit tests ==\n");
    test_dq_roundtrip();
    test_zero_sequence_free();
    test_known_value();
    test_midpoint_preserves_line_voltage();

    std::printf("---- %d checks, %d failures ----\n", g_checks, g_failures);
    if (g_failures == 0) {
        std::printf("RESULT unit_vector_conv PASS\n");
        return 0;
    }
    std::printf("RESULT unit_vector_conv FAIL\n");
    return 1;
}
