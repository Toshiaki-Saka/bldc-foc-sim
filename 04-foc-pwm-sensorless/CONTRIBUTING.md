# Contributing

Thank you for your interest in contributing to this project.

## How to contribute

1. **Fork** the repository and create a feature branch from `main`.
2. Make your changes in the feature branch.
3. Ensure the simulation still produces results consistent with `data/motor_log.csv`.
4. Open a pull request with a clear description of what changed and why.

## Code style

- C++20, no compiler extensions
- 4-space indentation, no tabs
- `[[nodiscard]]` on all functions that return computed values
- No raw owning pointers; use RAII

## Parameter changes

If you modify motor or controller parameters in `src/sim_params.hpp`, regenerate
`data/motor_log.csv` by running the simulation and copying the output:

```bash
./BrushlessDCMotor
cp data/sim_output.csv data/motor_log.csv
```

Include the updated reference file in your pull request.

## Reporting issues

Please open a GitHub issue with:

- Your OS and compiler version
- The exact command line used
- The full console output
