# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A `toon` command-line interface (`toon encode` / `toon decode`), installed automatically with the package and also runnable as `python -m toonbuilder`. Supports reading/writing files or stdin/stdout, input/output format auto-detection from file extensions, custom indentation, and XML root-element naming. See the README's [Command-Line Interface](README.md#command-line-interface) section.
- TOML support: a new `toml_to_toon` module with `encode`, `decode`, `encode_file`, and `decode_file`, mirroring the existing JSON/XML API. Parses via the standard-library `tomllib` on Python 3.11+; the optional `toml` package is needed on older Pythons or to serialize TOON back to TOML (`pip install "toonbuilder[toml]"`).
- Automated PyPI publishing via GitHub Actions, using [trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC) — no stored API tokens.
- A CI workflow that runs the test suite across Python 3.9/3.11/3.12/3.14 and verifies the package builds cleanly on every push and pull request.
- A pytest suite covering round-trips and regressions for the JSON, XML, and TOML modules.
- `py.typed` marker (PEP 561) so the package's type hints are usable by downstream type checkers, plus the corresponding `Typing :: Typed` classifier.
- `encode_file`/`decode_file` now create missing output directories automatically across all three modules.
- The package version is now derived from git tags at build time (`setuptools-scm`) instead of being hand-maintained.

### Fixed

- **XML conversion was broken beyond one level of nesting.** Elements were double-wrapped (`<a><b><c>1</c></b></a>` decoded incorrectly), and attributes on elements with text content were silently dropped. Both are fixed, along with correct reconstruction of repeated (list) elements and boolean casing on decode.
- **JSON round-trips could silently change types.** Strings that looked like numbers, booleans, or null (e.g. `"01234"`, `"1.0"`, `"true"`) decoded back as the wrong type. These are now quoted on encode so round-trips are lossless.
- **Tabular array detection was unsafe.** Arrays of objects containing nested values (dicts/lists) were incorrectly collapsed into CSV-style rows, producing unparseable output. Non-scalar rows now fall back to an expanded format that round-trips correctly.
- **`decode` ignored custom indentation.** TOON text encoded with a custom `indent_str` (tabs, 4 spaces, etc.) failed to decode, since the decoder assumed 2-space indentation. Decoding now auto-detects the indent width used.
- Non-tabular arrays (objects, mixed types, nested arrays/objects) now round-trip through JSON encode/decode; previously they didn't.
- **Bare top-level scalars didn't decode.** `decode(encode(x))` returned `{}` for any scalar `x` (e.g. `encode(42)` → `decode(...)` gave `{}` instead of `42`).
- **`decode` silently swallowed malformed input** instead of raising, despite documenting `Raises: ValueError`. Corrupted tabular arrays (declared length not matching actual rows, or rows with the wrong field count) and unparseable object lines now raise a descriptive `ValueError` instead of returning wrong or partial data.
- **`datetime.date`/`time`/`datetime` values lost their type on round-trip**, most notably breaking TOML datetimes (they came back as plain strings instead of native TOML datetime literals). They now round-trip correctly, without misinterpreting genuine strings that merely look like dates.
- **`NaN`/`Infinity` floats decoded back as strings** instead of floats; fixed with the same quoting-symmetry approach used elsewhere.

### Changed

- README rewritten with badges, a fuller Quick Start (including TOML), an API reference table, a "Type Handling" section documenting the lossless-JSON vs. coerced-XML behavior, and release documentation.
- Minimum supported Python raised from the previously-claimed `>=3.7` to `>=3.9`. 3.7 and 3.8 were never actually tested in CI and are both end-of-life.

## [0.1.0] - 2025-12-04

Initial tagged release. JSON and XML conversion to/from TOON.

[Unreleased]: https://github.com/0xPolybit/toonbuilder/compare/v0.1.0...main
[0.1.0]: https://github.com/0xPolybit/toonbuilder/releases/tag/v0.1.0
