# WAF++ PASS GitHub Action

Run [WAF++ PASS](https://waf2p.dev) scans in GitHub Actions and push the results
to your WAF++ server `/runs` endpoint.

## Features

- Installs the `wafpass` CLI automatically (unless already present).
- Scans Terraform, Bicep, CDK, or Pulumi IaC files.
- Pushes the full `wafpass-result.json` payload to `POST /runs`.
- Supports both **Bearer token** and **API key** authentication.
- Fails the workflow step based on configurable policies (`fail_on`).
- Automatically marks runs as CI/CD (`run: { is_cicd: true }`) and sets `triggered_by: github-actions`.
- Returns `run_id`, `score`, and `findings_count` as action outputs.

## Usage

Add the action to a workflow after checking out your repository:

```yaml
name: WAF++ PASS Scan

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  wafpass:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run WAF++ PASS
        uses: WAF2p/wafpass-action@v0.1.0
        with:
          server_url: https://wafpass.example.com
          api_token: ${{ secrets.WAFPASS_TOKEN }}
          scan_path: ./infra
          iac_framework: terraform
          project: my-service
          stage: prod
          fail_on: high
```

### Authenticate with an API key

```yaml
      - name: Run WAF++ PASS
        uses: WAF2p/wafpass-action@v0.1.0
        with:
          server_url: https://wafpass.example.com
          api_key: ${{ secrets.WAFPASS_API_KEY }}
          scan_path: ./infra
```

## Inputs

| Input            | Required | Default      | Description |
|------------------|----------|--------------|-------------|
| `server_url`     | yes      | —            | Base URL of the WAF++ server. |
| `api_token`      | no       | —            | Bearer token. Provide either this or `api_key`. |
| `api_key`        | no       | —            | Ingest API key (`X-Api-Key`). |
| `scan_path`      | yes      | `.`          | Path(s) to scan. Separate multiple paths with spaces. |
| `iac_framework`  | no       | `terraform`  | IaC plugin: `terraform`, `bicep`, `cdk`, `pulumi`. |
| `stage`          | no       | —            | Deployment stage, e.g. `dev`, `staging`, `prod`. |
| `project`        | no       | repo name    | Project / repo identifier. |
| `branch`         | no       | current ref  | Git branch name. |
| `git_sha`        | no       | current SHA  | Commit SHA. |
| `fail_on`        | no       | `fail`       | `fail`, `skip`, `any`, `low`, `medium`, `high`, `critical`, `never`. |
| `min_severity`   | no       | —            | Minimum severity to evaluate: `low`, `medium`, `high`, `critical`. |
| `controls_dir`   | no       | —            | Path to local WAF++ YAML controls. |
| `server_controls`| no       | `false`      | Fetch controls from the WAF++ server instead. |
| `fetch_controls` | no       | `false`      | Clone controls from the framework repo before scanning. |
| `framework_repo` | no       | `WAF2p/fr..` | Repo to fetch controls from when `fetch_controls` is enabled. |
| `verbose`        | no       | `false`      | Show all results including PASSes. |
| `plan_file`      | no       | —            | Path to a Terraform plan JSON for change overview. |
| `upload_source`  | no       | `false`      | Upload source files for dashboard diff previews. |
| `wafpass_version`| no       | —            | `wafpass-core` version to install. |
| `wafpass_source` | no       | —            | Override pip source, e.g. `git+https://github.com/WAF2p/pass.git`. |
| `python_version` | no       | `3.12`       | Python version for the runner. |

## Outputs

| Output           | Description |
|------------------|-------------|
| `run_id`         | UUID of the created run on the WAF++ server. |
| `score`          | Overall compliance score returned by the server. |
| `findings_count` | Number of findings in the scan result. |

## Fail policies

The `fail_on` input controls whether the action step fails **after** the result
has already been pushed to the server:

- `fail` — fail if any finding has status `FAIL`.
- `skip` / `any` — fail if any finding is `FAIL` or `SKIP`.
- `low`, `medium`, `high`, `critical` — fail if any finding has at least that severity.
- `never` — never fail the step.

## Installing the CLI

By default the action installs `wafpass-core` from PyPI. If your package is not
published yet, install from the source repository instead:

```yaml
      - name: Run WAF++ PASS
        uses: WAF2p/wafpass-action@v0.1.0
        with:
          server_url: ${{ vars.WAFPASS_SERVER_URL }}
          api_key: ${{ secrets.WAFPASS_API_KEY }}
          scan_path: ./infra
          wafpass_source: git+https://github.com/WAF2p/pass.git
```

## Multi-cloud / monorepo example

```yaml
      - name: Run WAF++ PASS
        uses: WAF2p/wafpass-action@v0.1.0
        with:
          server_url: ${{ vars.WAFPASS_SERVER_URL }}
          api_key: ${{ secrets.WAFPASS_API_KEY }}
          scan_path: ./aws ./azure ./gcp
          iac_framework: terraform
          project: ${{ github.repository }}
          stage: ${{ github.ref_name == 'main' && 'prod' || 'dev' }}
          fail_on: high
          upload_source: true
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).
