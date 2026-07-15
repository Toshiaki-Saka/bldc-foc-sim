<!-- Thank you for contributing. Please also review CONTRIBUTING.md. -->

## Summary of changes

<!-- Briefly describe what changed and why. Reference related issues with #number. -->

## Affected models / area

- [ ] 01-foc-ideal-voltage
- [ ] 02-foc-pwm-drive
- [ ] 03-foc-pwm-eps
- [ ] 04-foc-pwm-sensorless
- [ ] 05-foc-pwm-eps-sensorless
- [ ] Common (docs / CI / scripts / common)

## Checklist

- [ ] The models I touched build with `cmake --build`
- [ ] `ctest` passes (smoke + numerical tests)
- [ ] If I changed parameters in `sim_params.hpp` / `eps_sim_params.hpp`, I regenerated and included the regression reference CSVs
- [ ] I followed the code style (4-space indent, C++20, `[[nodiscard]]`)
- [ ] I updated the documentation (`docs_en/` / `docs_ja/` and the relevant `README.md`) as needed
