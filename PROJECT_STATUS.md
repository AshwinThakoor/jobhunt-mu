# JobHunt MU — Project Status

> 🚧 **Active Development**
>
> Current milestone: **Phase 1.6 — Resume Intelligence Engine V3**

JobHunt MU is an AI-assisted career platform being developed for job seekers in Mauritius and beyond.

This document separates functionality that already exists from functionality currently under development and future roadmap items.

## ✅ Implemented / Foundation Available

### Job Marketplace
- Multi-source job aggregation
- Mauritius-focused opportunities
- Remote opportunities
- Job search and filtering
- Job detail pages
- Categories and work modes
- Company/source information
- Saved-job foundation

### Job Data Pipeline
- Multi-source importer
- MyJob.mu importer
- Mauritius job-source integration
- Remotive integration
- Job normalization
- Duplicate-handling foundation
- Company image downloading
- Import tracking/data-quality foundation

### Resume & Matching Foundation
- Resume upload
- Resume parsing foundation
- Resume-to-job compatibility analysis
- Matched-skill explanations
- Missing/unclear skill detection
- Resume improvement recommendations
- Explainable score foundation

### Application Studio
- Job-specific application preparation
- CV selection
- Tailored-resume generation foundation
- Cover-letter generation
- Professional application-email generation
- Editable generated documents
- Saved career documents
- DOCX downloads

### Accounts & Premium
- Django authentication foundation
- User profiles
- Basic/Premium entitlement foundation
- Server-side Premium restrictions
- Stripe checkout/webhook foundation

### Engineering
- Django application
- Automated tests
- Environment-based configuration
- Docker/Docker Compose foundation
- GitHub workflow/configuration foundation
- Security and deployment documentation
- Development and troubleshooting documentation

---

## 🚧 Currently Being Built

# Phase 1.6 — Resume Intelligence Engine V3

The Resume Intelligence Engine is intended to become one of JobHunt MU's main technical differentiators.

Current work includes:

- Existing parser/matching-engine audit
- Structured resume representation
- Resume section detection
- Extraction confidence
- Skill normalization
- Skill ontology
- Exact vs related skill matching
- Evidence-strength analysis
- Job-requirement extraction
- Must-have vs preferred requirement classification
- Experience matching
- Education matching
- Seniority matching
- Hybrid compatibility scoring
- Score-confidence calculation
- Mandatory blocker detection
- Explainable evidence
- Truthfulness safeguards
- Matching evaluation framework
- Benchmark dataset design
- Ranking-quality evaluation
- Human-agreement evaluation
- Confidence calibration

### Important

JobHunt MU does **not** currently claim an arbitrary real-world "AI accuracy percentage."

Accuracy and ranking-quality claims will only be published after the Resume Intelligence Engine has been evaluated against a documented benchmark.

---

## 📋 Planned

### Resume Studio
- Professional resume builder
- Multiple templates
- Job-specific tailoring
- Editable AI recommendations
- Resume version history
- DOCX/PDF export

### Application Intelligence
- Advanced job-specific CV optimization
- Cover-letter intelligence
- Application-email assistant
- Application readiness checks
- Truthfulness/evidence verification

### Company Intelligence
- Company profiles
- Company history
- Leadership information where publicly available
- Locations
- Images
- Website/social information
- Available reviews/feedback
- Source attribution

### Application Tracker
- Saved applications
- Application stages
- Deadlines
- Notes
- Follow-up reminders
- Interview status

### Interview Intelligence
- Job-specific interview preparation
- Likely interview topics
- Practice questions
- Answer feedback
- Company/job context

### JobHunt AI
- Career assistant
- Job discovery assistance
- Resume guidance
- Application guidance
- Interview preparation

### Support
- AI-assisted 24/7 support
- Human escalation/contact workflow
- Help centre and FAQ

### Employer Platform
- Employer accounts
- Job posting
- Candidate management
- Recruiter dashboard
- Employer analytics

### Production Infrastructure
- PostgreSQL
- Redis/background jobs
- Scheduled import workers
- Monitoring
- Backups
- Production email
- Secure file storage
- Privacy/data-retention controls

### Commercial
- Complete Stripe subscription lifecycle
- Premium entitlements
- Billing management
- Cancellation
- Production pricing

### Release Path
- Feature-completeness gate
- Security/production gate
- Final UI/UX redesign
- Private beta
- MyJob.mu partnership demonstration
- Public beta
- Production launch

---

## Product Principle

JobHunt MU distinguishes between:

**Implemented** → working functionality already present in the project.

**Currently Being Built** → active engineering work that must not be represented as complete.

**Planned** → approved roadmap functionality that has not yet shipped.

This status document will be updated as development progresses.