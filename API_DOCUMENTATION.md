# API and web endpoint documentation

## Current interface model

JobHunt MU is currently a server-rendered Django application. It does **not** expose a stable public REST API. Routes may return HTML, redirects, files, or Stripe webhook responses.

## Public routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` and `/internships/` | Search and browse active opportunities |
| GET | `/internships/<id>/` | Opportunity detail |
| GET/POST | `/login/`, `/signup/` | Authentication |
| POST/GET | `/payments/webhook/` | Stripe-signed webhook endpoint |

## Authenticated candidate routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/dashboard/` | Candidate dashboard |
| GET/POST | `/profile/` | Profile management |
| GET/POST | `/cvs/` | Resume list and upload |
| GET/POST | `/cvs/<id>/analyze/` | Review and confirm extraction |
| GET | `/recommendations/` | Explainable matches |
| POST | `/recommendations/<id>/action/` | Save, dismiss, or update recommendation |
| GET | `/saved-jobs/` | Saved opportunities |
| GET/POST | `/internships/<id>/apply/` | Application submission |
| GET | `/applications/` | Application history |
| GET/POST | `/internships/<id>/studio/` | Application Studio |
| GET/POST | `/career-documents/<id>/` | Edit generated document |
| GET | `/career-documents/<id>/download/` | Download DOCX document |

## Employer and administrator routes

Employer routes support company and opportunity creation. Django Admin at `/admin/` provides operational management. Authorization must be reviewed before production deployment.

## Stripe webhook example

Local forwarding:

```bash
stripe listen --forward-to localhost:8000/payments/webhook/
```

The webhook must verify `Stripe-Signature` with `STRIPE_WEBHOOK_SECRET`; never trust client-side payment success alone.

## Future REST design

A future `/api/v1/` should use explicit serializers, token/session policy, pagination, throttling, OpenAPI schema generation, and contract tests. Candidate resources include:

```text
GET  /api/v1/opportunities/
GET  /api/v1/opportunities/{id}/
POST /api/v1/resumes/
GET  /api/v1/recommendations/
POST /api/v1/applications/
```

No current HTML endpoint should be treated as a stable external API contract.
