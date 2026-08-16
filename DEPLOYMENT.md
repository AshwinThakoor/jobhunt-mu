# Deployment

## Production requirements

- Linux container or managed Python platform;
- Gunicorn or equivalent WSGI server;
- managed relational database;
- private object storage for resumes and generated documents;
- HTTPS and secure cookies;
- environment-secret management;
- email provider;
- error monitoring, logs, backups, and uptime checks;
- separate worker/scheduler for imports before scaling.

## Docker build

```bash
docker build -t jobhunt-mu .
docker run --env-file .env -p 8000:8000 jobhunt-mu
```

## Pre-deployment commands

```bash
python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py test
```

## Security settings to enable

Set `DJANGO_DEBUG=false`, configure the exact allowed hosts, terminate TLS, and enable secure cookie/HSTS settings through environment-aware Django configuration before production. Do not serve private resumes directly from a public `/media/` URL.

## Stripe

Create a production webhook endpoint, store its signing secret securely, enforce idempotency, and test payment failures, retries, cancellation, refunds, and duplicate events.

## Rollback

Keep a previous image, database backup, migration plan, and documented rollback command. Test restore procedures before launch.

## Current Docker scope

The included Compose file is for reproducible development and portfolio demonstration. It is not a complete high-availability production stack.
