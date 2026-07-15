# Changelog

The format of this file follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- GitHub community-standard files: Issue / Pull Request templates,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CITATION.cff`, and this `CHANGELOG.md`.
- Mechanized code style via `.editorconfig` / `.clang-format`.
- Numerical unit tests (invertibility of the Clarke/Park transforms, checking the
  steady-state solution against analytical values, etc.).
- A workflow that automatically deploys the MkDocs site to GitHub Pages.
- Sharing of duplicated sources by extracting a common core (`common/`).
- English README (`README.md`).

### Changed
- Added warning promotion (`-Wall -Wextra`), a `clang-format` check, and a Sanitizer job to CI.
- Extended `build/` in `.gitignore` to `build*/`.

### Removed
- Stray work-in-progress files (`sim_viewer_updated.py` in several places, `voltage_output.imag.png`).

## [0.1.0] - 2025

### Added
- Initial public release of the 5-model structure (`01`–`05`). FOC basics, PWM drive,
  EPS mechanism, sensorless control, and the integrated model.
- Shared theory documentation (`docs/`), CTest smoke tests, and a 5-model × 2-OS
  build/test matrix via GitHub Actions.
