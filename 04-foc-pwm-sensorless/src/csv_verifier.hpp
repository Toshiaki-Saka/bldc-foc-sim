#pragma once
// =============================================================================
//  csv_verifier.hpp  —  CSV 回帰照合ユーティリティ — 宣言
// -----------------------------------------------------------------------------
//  プロジェクト : bldc-foc-sim / 04-foc-pwm-sensorless
//  シミュレーション結果 CSV をリファレンス CSV と列ごとに比較し、
//  最大/平均絶対誤差を求める関数を宣言する。
//
//  ライセンス   : MIT (リポジトリの LICENSE を参照)
// =============================================================================

#include <string>
#include <vector>

// Per-column error statistics between reference and simulation CSVs.
struct ColumnStats {
    std::string name;
    double max_abs_error  = 0.0;
    double mean_abs_error = 0.0;
};

struct VerifyResult {
    std::vector<ColumnStats> columns;
    int  total_rows     = 0;
    bool ref_available  = false;  // false when reference file could not be opened
};

// Compare ref_path vs sim_path row-by-row.
// Writes absolute differences to diff_path (CSV).
// Returns per-column statistics.
[[nodiscard]] VerifyResult verify_csv(
    const std::string& ref_path,
    const std::string& sim_path,
    const std::string& diff_path);
