# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-08-14

### Changed

- Migrated result ingestion to the versioned `/api/v1/runs` endpoint. `server_url` must now point to a server that serves `/api/v1/*`.

### Added

- New `fetch_controls` input to clone the WAF++ framework controls before scanning.
- New `framework_repo` input to select the source repository when `fetch_controls` is enabled.

## [0.1.0] - 2026-07-17

### Added

- Initial release of the WAF++ PASS GitHub Action.
- Installs the `wafpass` CLI automatically and scans Terraform, Bicep, CDK, or Pulumi IaC files.
- Pushes the full `wafpass-result.json` payload to the WAF++ server.
- Supports Bearer token (`api_token`) and API key (`api_key`) authentication.
- Configurable failure policies via `fail_on`.
- CI/CD metadata injection (`is_cicd`, `triggered_by: github-actions`).
- Action outputs: `run_id`, `score`, and `findings_count`.

[Unreleased]: https://github.com/WAF2p/wafpass-action/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/WAF2p/wafpass-action/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/WAF2p/wafpass-action/releases/tag/v0.1.0
