# Architecture

## System context

```mermaid
C4Context
    title JobHunt MU system context
    Person(candidate, "Candidate", "Searches jobs, uploads resumes, prepares applications")
    Person(employer, "Employer", "Creates companies and opportunities")
    Person(admin, "Administrator", "Operates imports, content, payments, and users")
    System(jobhunt, "JobHunt MU", "Django recruitment and career platform")
    System_Ext(sources, "Opportunity providers", "Public pages, feeds, and approved APIs")
    System_Ext(stripe, "Stripe", "Hosted checkout and signed events")
    Rel(candidate, jobhunt, "Uses")
    Rel(employer, jobhunt, "Uses")
    Rel(admin, jobhunt, "Operates")
    Rel(jobhunt, sources, "Fetches permitted opportunity data")
    Rel(jobhunt, stripe, "Creates checkout sessions and verifies webhooks")
```

## Containers

```mermaid
flowchart TB
    Browser --> Django[Django web process]
    Django --> Templates[Templates and static assets]
    Django --> Services[CV analyzer, matcher, application studio]
    Django --> ORM[Django ORM]
    ORM --> DB[(SQLite local / MySQL configured)]
    Django --> Media[(Private media storage required in production)]
    Importer[CLI source importer] --> Sources[External permitted sources]
    Importer --> ORM
    Stripe[Stripe] --> Webhook[Signed webhook endpoint]
    Webhook --> ORM
```

## Main modules

- `myapp/models.py`: persistent domain model.
- `myapp/views.py`: server-rendered request orchestration and access control.
- `myapp/services/cv_analyzer.py`: PDF/DOCX extraction and candidate evidence detection.
- `myapp/services/job_matcher.py`: deterministic, explainable compatibility scoring.
- `myapp/services/application_studio.py`: grounded draft generation.
- `scrape_jobs.py`: normalized multi-source ingestion.
- `scrape_myjobmu.py`: MyJob-specific collection support.
- `myapp/management/commands/archive_stale_jobs.py`: lifecycle maintenance.

## Recommendation flow

```mermaid
sequenceDiagram
    actor User
    participant Web as Django view
    participant CV as CV analyzer
    participant Match as Job matcher
    participant DB as Database
    User->>Web: Upload resume
    Web->>CV: Extract text and skills
    CV-->>Web: Extraction result and warnings
    Web->>DB: Save parsed evidence
    User->>Web: Open AI matches
    Web->>Match: Compare primary CV with active jobs
    Match-->>Web: Score, confidence, matches, gaps
    Web->>DB: Upsert recommendations
    Web-->>User: Explainable ranked results
```

## Architectural decisions

1. **Django monolith:** appropriate for an early-stage product because authentication, ORM, templates, admin, and payments remain cohesive.
2. **Service modules:** matching and document logic are separated from views so they can later become APIs or workers.
3. **Explainability first:** deterministic evidence is preferred over an opaque hiring prediction.
4. **CLI ingestion:** importers run independently from web requests and can later move to Celery/Redis.
5. **Hosted payment UI:** Stripe Checkout reduces payment-card handling scope.

## Known architectural gaps

- Production-grade private object storage is not implemented.
- Long-running imports are not yet queued through a worker system.
- No public versioned REST API exists.
- Database support is optimized for local SQLite and configurable MySQL; production PostgreSQL support is planned.
- The Django app is broad and should eventually be split into `accounts`, `opportunities`, `resumes`, `matching`, `applications`, `billing`, and `ingestion` apps.
