# Contributing to WAF++ PASS GitHub Action

Thank you for your interest in improving the WAF++ PASS GitHub Action.

## How to contribute

1. Open an issue describing the bug or enhancement.
2. Fork the repository and create a feature branch.
3. Make your changes, ensuring the self-test workflow still passes.
4. Submit a pull request referencing the issue.

## Development

Run the local syntax checks:

```bash
python3 -m pip install pyyaml
python3 -c "import yaml; yaml.safe_load(open('action.yml'))"
python3 -m py_compile run.py
```

## License

By contributing, you agree that your contributions will be licensed under the Apache-2.0 License.
