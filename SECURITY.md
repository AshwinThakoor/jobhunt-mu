# Security policy

## Supported versions

Until the first stable release, security fixes target the latest `main` branch and latest tagged release.

## Reporting a vulnerability

Do not open a public issue. Use GitHub private vulnerability reporting or the private security contact configured by the maintainer. Include impact, affected route/module, reproduction steps, and suggested mitigation. Expect acknowledgement within seven days once a monitored contact is configured.

## Sensitive data

Never commit or share:

- `.env` files or API keys;
- uploaded resumes or generated career documents;
- SQLite/MySQL dumps;
- Stripe customer, session, or payment identifiers;
- real application data;
- private source credentials;
- server logs containing resume text.

## Production security gaps

Before public deployment, implement MIME/content validation, upload size limits, malware scanning, private object storage, authorized download views, CSRF and session review, secure cookies, HSTS, rate limiting, webhook idempotency, audit logging, dependency scanning, data retention, export, and account deletion.

## AI safety and integrity

The platform must not invent candidate experience, represent match scores as hiring probabilities, or use protected traits in ranking. Users must review generated application content.
