#pragma once
// =============================================================================
//  csv_verifier.hpp  —  CSV regression comparison utility — declarations
// -----------------------------------------------------------------------------
//  Project     : bldc-foc-sim (shared across all models)
//  Declares the function that compares a simulation-result CSV against a
//  reference CSV column by column and computes the maximum/mean absolute error.
//
//  NOTE: This file is identical across all models (01-05). When changing it,
//        propagate the change to every model. CI (the consistency job) checks
//        cross-model equality and detects drift.
//
//  License     : MIT (see LICENSE at repo root)
// =============================================================================

#include <string>
#include <vector>

// Per-column error statistics between reference and simulation CSVs.
struct ColumnStats {
    std::string name;
    double      max_abs_error  = 0.0;
    double      mean_abs_error = 0.0;
};

struct VerifyResult {
    std::vector<ColumnStats> columns;
    int                      total_rows    = 0;
    bool                     ref_available = false; // false when reference file could not be opened
};

// Compare ref_path vs sim_path row-by-row.
// Writes absolute differences to diff_path (CSV).
// Returns per-column statistics.
[[nodiscard]] VerifyResult verify_csv(const std::string& ref_path, const std::string& sim_path,
                                      const std::string& diff_path);
