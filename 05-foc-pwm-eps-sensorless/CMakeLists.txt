# =============================================================================
#  BLDC FOC シミュレーション — PWM + EPS + センサーレスモデル (Model 05)
# -----------------------------------------------------------------------------
#  プロジェクト : bldc-foc-sim  /  05-foc-pwm-eps-sensorless
#  概要         : FOC + PWM + EPS + 位置センサーレス制御の統合モデル
#
#  ビルド方法:
#      cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
#      cmake --build build --config Release
#
#  生成物       : BrushlessDCMotor, EpsGearboxSim
#                 (実行ファイルはプロジェクト直下に出力される)
#
#  必要環境:
#      - C++20 対応コンパイラ (GCC 11+, Clang 14+, MSVC 2022)
#      - CMake 3.16 以上
#      - Eigen3 3.4 以上 (線形代数ライブラリ)
#
#  ライセンス   : MIT (LICENSE ファイル参照)
# =============================================================================

cmake_minimum_required(VERSION 3.16)
project(BrushlessDCMotor
    VERSION     1.0.0
    DESCRIPTION "FOC + PWM + EPS + 位置センサーレス制御の統合モデル"
    LANGUAGES   CXX)

# --- C++ standard --------------------------------------------------------------
# 本プロジェクトは std::format / std::numbers / 指示付き初期化など C++20 の
# 機能を使用するため、C++20 を必須とする。
set(CMAKE_CXX_STANDARD          20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS        OFF)

# --- ビルドタイプ既定値 --------------------------------------------------------
# 単一構成ジェネレータ (Makefile / Ninja) でビルドタイプ未指定の場合は
# Release を既定とする (最適化を有効化)。
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# --- コンパイラ個別設定 --------------------------------------------------------
if(MSVC)
    # MSVC ではソース・実行時とも UTF-8 として扱う (日本語コメント対策)。
    add_compile_options(/utf-8)
endif()

# --- 依存ライブラリ : Eigen3 ---------------------------------------------------
# まずシステムインストール済みの Eigen3 を検索する。
find_package(Eigen3 3.4 QUIET CONFIG)
if(NOT Eigen3_FOUND)
    # 見つからない場合は FetchContent でソースを取得してフォールバックする
    # (この場合はビルド時にネットワーク接続が必要)。
    message(STATUS "Eigen3 not found - fetching via FetchContent")
    include(FetchContent)
    FetchContent_Declare(Eigen3
        GIT_REPOSITORY https://gitlab.com/libeigen/eigen.git
        GIT_TAG        3.4.0)
    FetchContent_MakeAvailable(Eigen3)
else()
    message(STATUS "Eigen3 found: ${Eigen3_VERSION}")
endif()

# --- ターゲット : BrushlessDCMotor -----------------------------------------------
#  センサーレス制御のモータ単体シミュレーション (Model 04 相当)。
add_executable(BrushlessDCMotor
    src/main.cpp
    src/motor_vector_conv.cpp
    src/motor_controller.cpp
    src/motor_model.cpp
    src/sensorless_observer.cpp
    src/csv_verifier.cpp)

target_include_directories(BrushlessDCMotor PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src)

target_link_libraries(BrushlessDCMotor PRIVATE Eigen3::Eigen)

# 実行ファイルはプロジェクト直下に出力する (data/ や scripts/ から
# 相対パスでアクセスしやすくするため)。
set_target_properties(BrushlessDCMotor PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY         ${CMAKE_CURRENT_SOURCE_DIR}
    RUNTIME_OUTPUT_DIRECTORY_DEBUG   ${CMAKE_CURRENT_SOURCE_DIR}
    RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_CURRENT_SOURCE_DIR})

# --- ターゲット : EpsGearboxSim -----------------------------------------------
#  センサーレス制御 + EPS 機構の統合シミュレーション。
add_executable(EpsGearboxSim
    src/eps_main.cpp
    src/eps_gearbox_model.cpp
    src/eps_controller.cpp
    src/motor_vector_conv.cpp
    src/motor_controller.cpp
    src/motor_model.cpp)

target_include_directories(EpsGearboxSim PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src)

target_link_libraries(EpsGearboxSim PRIVATE Eigen3::Eigen)

# 実行ファイルはプロジェクト直下に出力する (data/ や scripts/ から
# 相対パスでアクセスしやすくするため)。
set_target_properties(EpsGearboxSim PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY         ${CMAKE_CURRENT_SOURCE_DIR}
    RUNTIME_OUTPUT_DIRECTORY_DEBUG   ${CMAKE_CURRENT_SOURCE_DIR}
    RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_CURRENT_SOURCE_DIR})

# --- スモークテスト (CTest) -----------------------------------------------------
#  P1: 最小の自動回帰テスト。golden 値ではなく「ビルドでき、短時間実行で RESULT 行を
#  NaN/Inf なく出力する」実行健全性を担保する。CI から ctest で一括実行される。
enable_testing()
add_test(NAME smoke_BrushlessDCMotor
         COMMAND BrushlessDCMotor --span 0.05 --no_csv --quiet)
set_tests_properties(smoke_BrushlessDCMotor PROPERTIES
    PASS_REGULAR_EXPRESSION "RESULT "
    FAIL_REGULAR_EXPRESSION "nan|inf|NaN|Inf")
