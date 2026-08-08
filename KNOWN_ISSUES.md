# Known issues

1. The domain model `Internship` represents all opportunity types and should be renamed.
2. Resume file extension validation does not by itself verify MIME type or file safety.
3. Uploaded media is served locally in development; production requires private object storage and authorized downloads.
4. Imports run synchronously from CLI and lack Celery/Redis scheduling.
5. External parsers may break when source websites change.
6. The matching score is heuristic and has not yet been validated on a labelled benchmark.
7. Generated application drafts require user review and must not imply unsupported experience.
8. Premium state is a boolean rather than a full subscription lifecycle.
9. SQLite is suitable for development but not the preferred production database.
10. Email verification, password-reset delivery, and operational alerts require a production email provider.
11. Some legacy student-record views and templates remain in the repository.
12. Public company intelligence and review moderation are not complete.

See [ROADMAP.md](ROADMAP.md) for remediation priorities.
