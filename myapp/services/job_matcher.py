"""Explainable resume-to-job compatibility scoring."""
from __future__ import annotations
import re
from typing import Iterable
from .cv_analyzer import SKILL_TERMS

SKILL_ALIASES = {
    'mysql': 'sql', 'postgresql': 'sql', 'postgres': 'sql', 'mssql': 'sql',
    'ms excel': 'excel', 'microsoft excel': 'excel', 'spreadsheets': 'excel',
    'powerbi': 'power bi', 'power-bi': 'power bi', 'data visualisation': 'data visualization',
    'tableau desktop': 'tableau', 'python programming': 'python',
    'machine-learning': 'machine learning', 'ml': 'machine learning',
    'artificial intelligence': 'ai', 'customer support': 'customer service',
    'client service': 'customer service', 'client support': 'customer service',
    'reporting': 'data analysis', 'data reporting': 'data analysis',
    'business intelligence': 'power bi', 'ms office': 'microsoft office',
}
RELATED_SKILLS = {
    'sql': {'database', 'data analysis'}, 'excel': {'data analysis', 'microsoft office'},
    'power bi': {'data visualization', 'data analysis'}, 'tableau': {'data visualization'},
    'python': {'programming', 'data analysis'}, 'r': {'programming', 'data analysis'},
    'customer service': {'communication', 'client relationship'},
}

def _normalise(value: str) -> str:
    text = re.sub(r"\s+", " ", (value or '').strip().lower())
    return SKILL_ALIASES.get(text, text)

def _canonical(skill: str) -> str:
    return SKILL_ALIASES.get(_normalise(skill), _normalise(skill))

def extract_known_skills(text: str, extra_terms: Iterable[str] = ()) -> list[str]:
    haystack = f" {_normalise(text)} "
    raw_terms = {str(x).strip().lower() for x in SKILL_TERMS if str(x).strip()}
    raw_terms.update(str(x).strip().lower() for x in extra_terms if str(x).strip())
    raw_terms.update(SKILL_ALIASES)
    found=set()
    for raw in sorted(raw_terms, key=lambda x: (-len(x), x)):
        pattern = r"(?<![a-z0-9+#])" + re.escape(raw) + r"(?![a-z0-9+#])"
        if re.search(pattern, haystack): found.add(_canonical(raw))
    return sorted(found)

def _tokens(text: str) -> set[str]:
    stop={'and','the','with','for','from','this','that','you','your','our','job','role','work','years','skills','required','preferred'}
    return {w for w in re.findall(r"[a-z][a-z0-9+#.-]{2,}", _normalise(text)) if w not in stop}

def _related_matches(candidate: set[str], required: set[str]) -> list[str]:
    related=[]
    for needed in required:
        concepts=RELATED_SKILLS.get(needed, set())
        if concepts & candidate: related.append(needed)
        elif any(needed in RELATED_SKILLS.get(have, set()) for have in candidate): related.append(needed)
    return sorted(set(related))

def match_resume_to_job(*, resume_text: str, profile_skills: Iterable[str], job) -> dict:
    profile={_canonical(str(x)) for x in profile_skills if str(x).strip()}
    candidate=set(extract_known_skills(resume_text, profile)) | profile
    job_text=' '.join([job.title or '', job.description or '', job.requirements or '', job.responsibilities or '', ' '.join(job.skills_required or [])])
    required=set(extract_known_skills(job_text, job.skills_required or []))
    exact=sorted(candidate & required)
    related=_related_matches(candidate, required-set(exact))
    missing=sorted(required-set(exact)-set(related))
    if required:
        skill_score=(len(exact)+0.55*len(related))/len(required)
    else: skill_score=0.45
    resume_tokens=_tokens(resume_text); title_tokens=_tokens(job.title); job_tokens=_tokens(job_text)
    role_score=len(resume_tokens & title_tokens)/max(1,len(title_tokens))
    context_score=min(1.0,len(resume_tokens & job_tokens)/max(1,min(len(job_tokens),35)))
    location_score=0.5
    location=_normalise(job.location); profile_lower=_normalise(resume_text)
    if job.work_mode=='remote' or 'remote' in location: location_score=0.8
    elif location and location in profile_lower: location_score=1.0
    completeness=min(1.0,len(resume_text.strip())/1800)
    total=skill_score*.50+role_score*.18+context_score*.14+location_score*.08+completeness*.10
    total=max(.05,min(.98,total))
    confidence='high' if len(required)>=3 and len(resume_text)>=500 else ('medium' if required and len(resume_text)>=120 else 'low')
    breakdown={'skills':round(skill_score*100),'role_relevance':round(role_score*100),'keyword_context':round(context_score*100),'location_work_mode':round(location_score*100),'resume_completeness':round(completeness*100)}
    reasons=[]
    if exact: reasons.append(f"Exact matches: {', '.join(exact[:5])}")
    if related: reasons.append(f"Related skills: {', '.join(related[:4])}")
    if role_score>=.35: reasons.append('Your CV language aligns with the job title')
    if not reasons: reasons.append('Some transferable keywords were found, but stronger job-specific evidence is needed')
    return {'score':round(total,4),'reason':'; '.join(reasons),'matched_skills':exact,'related_skills':related,'missing_skills':missing[:12],'score_breakdown':breakdown,'match_confidence':confidence}
