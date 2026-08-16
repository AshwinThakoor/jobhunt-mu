# Testing

## Local checks

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
ruff check .
ruff format --check .
```

## Existing coverage areas

The Django test suite covers public job browsing, filters, premium visibility, Stripe flows, scraper parsing, resume extraction, matching, data-quality behavior, and Application Studio access.

## Missing high-priority tests

- authorization tests for every resume and generated-document route;
- malicious and oversized file uploads;
- webhook replay and idempotency;
- importer partial failures, timeouts, and archiving safeguards;
- concurrency around primary resumes and application counts;
- end-to-end browser tests for signup, upload, recommendations, and payment;
- accessibility checks;
- performance tests with thousands of opportunities;
- regression fixtures for external-source parser changes.

## CI

`.github/workflows/ci.yml` runs dependency installation, Django checks, migration drift detection, tests, and Ruff on supported Python versions.

## Test data

Use synthetic data only. Never place real resumes, private application content, payment identifiers, or redistributed scraped datasets in fixtures.
