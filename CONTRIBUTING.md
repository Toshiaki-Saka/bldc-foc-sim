# Contributing

Thank you for your interest in contributing to this repository (`bldc-foc-sim`).
This project is a courseware repository for learning FOC of BLDC/PMSM motors step by
step through five models (`01`–`05`). Each model can be built and run independently.

## Contribution flow

1. **Fork** the repository and cut a feature branch from `main`.
2. Make your changes.
3. Confirm that the models you touched build and that the smoke tests pass (see below).
4. Open a Pull Request clearly stating what you changed and why.

## Build and test

Each model is a separate CMake project (with the shared executable name `BrushlessDCMotor`).

```bash
# Example: build and test model 02
cmake -S 02-foc-pwm-drive -B 02-foc-pwm-drive/build -DCMAKE_BUILD_TYPE=Release
cmake --build 02-foc-pwm-drive/build --config Release
ctest --test-dir 02-foc-pwm-drive/build -C Release --output-on-failure
```

`ctest` runs a minimal smoke test (a short run checking that the `RESULT` line is
emitted free of NaN/Inf). The same steps are also run automatically in CI (GitHub
Actions) across a 5-model × Ubuntu/Windows matrix.

> Note: because all models use the same target name `BrushlessDCMotor`, the five
> models cannot be combined into a single CMake tree. Please configure / build / test
> **each model individually**.

## Code style

- C++20, with compiler extensions disabled (`CMAKE_CXX_EXTENSIONS OFF`)
- Indent with 4 spaces; tabs are not allowed
- Use `[[nodiscard]]` on functions that return a computed result
- Avoid ownership via raw pointers; use RAII
- Formatting follows the `.clang-format` bundled with the repository (auto-format with
  `clang-format -i <file>`). CI (the `lint` job) checks for deviations.
- Must build cleanly at a high warning level (`-Wall -Wextra` / `/W4`). CI treats
  warnings as errors with `-DBLDC_WARNINGS_AS_ERRORS=ON`.

## Files shared across models

Each model is self-contained (it keeps all sources under `src/`), but utilities that
are **meant to be identical across all models** are physically duplicated. These must
remain byte-for-byte identical across models, and CI (the `consistency` job) checks
that they match.

Target files (under each model's `src/`):

- `motor_vector_conv.hpp` / `motor_vector_conv.cpp` (Clarke / Park transforms, midpoint modulation)
- `csv_verifier.hpp` / `csv_verifier.cpp` (CSV regression checking)

If you change any one of them, please **apply the identical content to all models**.
Locally, you can verify they match with the following command (run at the repository root).

```bash
bash tests/check_shared_files.sh
```

## Updating regression references when changing parameters

If you change the motor / control parameters in `src/sim_params.hpp` (or
`eps_sim_params.hpp`), regenerate the reference CSV and include it in your PR.

```bash
./BrushlessDCMotor
cp data/sim_output.csv data/motor_log.csv
```

## Reporting issues

Please attach the following to your GitHub Issue.

- OS and compiler version
- The exact command line you ran
- The full console output
