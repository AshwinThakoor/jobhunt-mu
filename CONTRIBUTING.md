# Contributing

Thank you for improving JobHunt MU.

## Workflow

1. Open or reference an issue.
2. Fork the repository and create a focused branch.
3. Add tests and documentation with the change.
4. Run `pre-commit run --all-files` and `python manage.py test`.
5. Submit a pull request using the template.

## Principles

- Never commit personal resumes, secrets, database files, live payment data, or redistributed job datasets.
- Respect external-source terms and rate limits.
- Keep matching explanations truthful and avoid unsupported hiring claims.
- Generated application content must remain grounded in user-provided facts.
- Prefer small, reviewable changes.

## Commit style

Use imperative, scoped messages such as `docs: explain matching limitations` or `fix: enforce CV ownership in download view`.

## Development setup

See [INSTALLATION.md](INSTALLATION.md). Architecture-changing proposals should include an ADR under `docs/adr/`.
