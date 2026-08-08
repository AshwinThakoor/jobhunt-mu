"""Transparent application document generator.

This module does not call an external AI service. It produces editable first drafts
from the user's own CV evidence and the selected job, and never invents experience.
"""
from __future__ import annotations
import re
from .job_matcher import match_resume_to_job


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _sentences(text: str, limit: int = 6) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    return [p.strip(" •-\t") for p in parts if len(p.strip()) >= 25][:limit]


def build_application_pack(*, user, cv, job) -> dict:
    profile = user.userprofile
    resume_text = cv.extracted_text or ""
    match = match_resume_to_job(
        resume_text=resume_text,
        profile_skills=profile.skills or cv.extracted_skills or [],
        job=job,
    )
    name = user.get_full_name().strip() or user.username
    matched = match["matched_skills"]
    related = match.get("related_skills", [])
    missing = match["missing_skills"]
    evidence = _sentences(resume_text, 5)
    evidence_text = evidence[0] if evidence else "My attached CV outlines my relevant education, projects and experience."
    skills_text = ", ".join((matched + related)[:6]) or "relevant transferable skills"

    summary = (
        f"Candidate for {job.title} with evidence of {skills_text}. "
        f"The profile should emphasize verified projects, education and outcomes that relate directly to {job.company.name}."
    )
    improvement_actions = []
    for skill in missing[:5]:
        improvement_actions.append({
            "title": f"Address {skill}",
            "guidance": f"Add {skill} only where your CV can support it with a real course, project or work example. Otherwise leave it as a development goal.",
        })
    if not improvement_actions:
        improvement_actions.append({
            "title": "Strengthen evidence",
            "guidance": "Add measurable outcomes to the most relevant bullets, without changing the facts.",
        })

    cover_letter = f"""Dear Hiring Team,

I am applying for the {job.title} opportunity at {job.company.name}. My background includes {skills_text}, which aligns with key parts of the role.

One example from my CV is: {evidence_text}

I am particularly interested in this opportunity because it would allow me to contribute to {job.company.name} while continuing to develop in {job.company.industry or 'the organisation’s field'}. I would welcome the opportunity to discuss how my verified experience, projects and learning can support your team.

Thank you for your consideration.

Kind regards,
{name}"""

    application_email = f"""Subject: Application for {job.title} – {name}

Dear Hiring Team,

Please find attached my application for the {job.title} position at {job.company.name}. My CV highlights experience and projects involving {skills_text}.

I would be grateful for the opportunity to discuss my application. Thank you for your time and consideration.

Kind regards,
{name}
{user.email or ''}"""

    tailored_resume = f"""{name}
{user.email or ''}

TARGET ROLE
{job.title} — {job.company.name}

TAILORED PROFESSIONAL SUMMARY
{summary}

RELEVANT VERIFIED SKILLS
{skills_text}

SELECTED EVIDENCE FROM ORIGINAL CV
""" + "\n".join(f"• {item}" for item in evidence) + """

IMPORTANT
Review every line before use. This draft only reorganizes text found in your profile/CV and does not certify that you meet every requirement.
"""

    return {
        "match": match,
        "summary": summary,
        "improvement_actions": improvement_actions,
        "cover_letter": cover_letter,
        "application_email": application_email,
        "tailored_resume": tailored_resume,
    }
