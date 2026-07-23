// =============================================================================
//  csv_verifier.cpp  —  CSV regression comparison utility — implementation
// -----------------------------------------------------------------------------
//  Project : bldc-foc-sim (shared across all models)
//  Reads two CSVs, computes the differences of their common columns, and writes
//  a diff CSV. Used to detect regressions when the code is changed.
//
//  NOTE: This file is identical across all models (01-05). When changing it,
//        propagate the change to every model. The CI (consistency job) checks
//        that the models match and detects any drift.
//
//  License : Apache-2.0 (see LICENSE at repo root)
// =============================================================================

#include "csv_verifier.hpp"
#include <cmath>
#include <format>
#include <fstream>
#include <sstream>

namespace {

std::vector<std::string> parse_header(const std::string& line) {
    std::vector<std::string> cols;
    std::stringstream        ss(line);
    std::string              cell;
    while (std::getline(ss, cell, ','))
        cols.push_back(cell);
    return cols;
}

std::vector<double> parse_row(const std::string& line) {
    std::vector<double> row;
    std::stringstream   ss(line);
    std::string         cell;
    while (std::getline(ss, cell, ','))
        row.push_back(std::stod(cell));
    return row;
}

} // namespace

VerifyResult verify_csv(const std::string& ref_path, const std::string& sim_path,
                        const std::string& diff_path) {
    VerifyResult result;

    std::ifstream ref_file(ref_path);
    std::ifstream sim_file(sim_path);

    if (!ref_file.is_open() || !sim_file.is_open()) {
        result.ref_available = false;
        return result;
    }
    result.ref_available = true;

    // Headers
    std::string ref_header, sim_header;
    std::getline(ref_file, ref_header);
    std::getline(sim_file, sim_header);

    const auto col_names = parse_header(ref_header);
    const int  n_cols    = static_cast<int>(col_names.size());

    result.columns.resize(n_cols);
    for (int i = 0; i < n_cols; ++i)
        result.columns[i].name = col_names[i];

    std::vector<double> sum_err(n_cols, 0.0);
    std::vector<double> max_err(n_cols, 0.0);

    // Diff CSV header: row + one diff column per signal column
    std::ofstream diff_file(diff_path);
    {
        std::string header = "row";
        for (const auto& name : col_names)
            header += std::format(",{}_diff", name);
        diff_file << header << "\n";
    }

    std::string ref_line, sim_line;
    int         row = 0;
    while (std::getline(ref_file, ref_line) && std::getline(sim_file, sim_line)) {
        const auto ref_row = parse_row(ref_line);
        const auto sim_row = parse_row(sim_line);

        diff_file << row;
        for (int c = 0; c < n_cols; ++c) {
            const double abs_err = std::abs(ref_row[c] - sim_row[c]);
            diff_file << std::format(",{}", abs_err);
            sum_err[c] += abs_err;
            max_err[c] = std::max(max_err[c], abs_err);
        }
        diff_file << "\n";
        ++row;
    }

    result.total_rows = row;
    for (int c = 0; c < n_cols; ++c) {
        result.columns[c].max_abs_error  = max_err[c];
        result.columns[c].mean_abs_error = row > 0 ? sum_err[c] / row : 0.0;
    }

    return result;
}
