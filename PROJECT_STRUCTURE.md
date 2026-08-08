# Project structure

```text
.
├── .github/                 GitHub workflows and community templates
├── data/samples/            Synthetic examples only
├── docs/                    Documentation index, audit, and assets
├── media/                   Runtime uploads; ignored except .gitkeep
├── myapp/
│   ├── management/commands/ Operational commands
│   ├── migrations/          Django schema history
│   ├── services/            Resume, matching, and document logic
│   ├── static/              Application CSS and owned images
│   ├── templates/           Server-rendered UI
│   ├── admin.py             Admin registrations
│   ├── forms.py             Form validation
│   ├── models.py            Domain persistence
│   ├── tests.py             Django test suite
│   ├── urls.py              Application routes
│   └── views.py             Request orchestration
├── myproject/               Django settings and entry points
├── scrape_jobs.py           Multi-source importer
├── scrape_myjobmu.py        MyJob source support
├── Dockerfile               Container image
├── docker-compose.yml       Local container orchestration
├── pyproject.toml           Tooling configuration
└── manage.py                Django command entry point
```

## Recommended future split

As the codebase grows, separate Django apps into `accounts`, `companies`, `opportunities`, `resumes`, `matching`, `applications`, `billing`, and `ingestion`. Do this through incremental migrations rather than a single disruptive rewrite.
