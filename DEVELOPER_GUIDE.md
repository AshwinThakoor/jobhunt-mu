# Developer guide

## Request lifecycle

A browser request enters `myproject/urls.py`, is delegated to `myapp/urls.py`, handled by a view, validated through a form when applicable, and persisted through Django models. Domain-heavy work should be delegated to `myapp/services/` rather than embedded in views.

## Adding a model change

```bash
python manage.py makemigrations myapp
python manage.py migrate
python manage.py test
```

Review generated migrations before committing. Never edit an already-released migration unless the project has not been shared or deployed.

## Adding a source connector

1. Confirm permission, terms, authentication, and rate limits.
2. Implement a `JobSource` subclass in `scrape_jobs.py` or a dedicated source module.
3. Normalize output to the common record schema.
4. Add deterministic parser fixtures and tests.
5. Add retry, timeout, and failure isolation.
6. Document the source and required environment variables.
7. Do not archive missing records unless the refresh was complete and successful.

## Changing matching logic

- Preserve an explanation for every score component.
- Version dictionaries and weights.
- Add regression cases for exact, related, missing, and ambiguous skills.
- Do not represent compatibility as hiring probability.
- Record evaluation evidence in `PERFORMANCE.md` before marketing accuracy claims.

## Adding a view

- Require authentication where appropriate.
- Filter objects by the requesting user before reading or mutating them.
- Validate POST data with a form.
- Use POST for state changes and retain CSRF protection.
- Add success, failure, authorization, and ownership tests.
- Document the route in `API_DOCUMENTATION.md`.

## Generated documents

Generated content must be grounded in confirmed resume and job facts. Keep original and proposed content distinguishable, require user review, and avoid unsupported achievements.

## Definition of done

A change is complete when code, tests, docs, migrations, security considerations, accessibility, and rollback implications have been reviewed.
