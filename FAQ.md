# FAQ

## Is this a trained AI model?

Not currently. Matching uses resume/job text extraction, known-skill normalization, deterministic weighting, and explainable evidence. The repository does not claim to contain a proprietary trained foundation model.

## Does a match score predict hiring?

No. It estimates textual and structured compatibility only. Hiring depends on many factors outside the system.

## Can I scrape LinkedIn or Upwork with this project?

The project intentionally avoids unauthorized scraping. Use official links, feeds, or approved APIs and comply with provider terms.

## Why are there fewer jobs than on a source website?

Limits, pagination, filters, source failures, duplicates, or expired records may reduce counts. Review importer logs and `ImportRun` records.

## Why is `myapp_importrun` missing?

Apply migrations with `python manage.py migrate` in the active virtual environment and confirm with `python manage.py showmigrations myapp`.

## Can I use SQLite in production?

It is appropriate for local development and small demos. Use a managed relational database for a public multi-user deployment.

## Are uploaded resumes safe?

Not by default merely because they are in Django. Production needs private storage, MIME validation, malware scanning, access checks, retention rules, and deletion support.

## How do I test Premium?

Use Stripe test keys and Stripe CLI, or set a test user's premium flag in a non-production environment. Never bypass payment checks in production.
