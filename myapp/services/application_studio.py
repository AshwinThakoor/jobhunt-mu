"""Public portfolio boundary for the JobHunt MU Application Studio.

The private project generates grounded application drafts from candidate evidence and
selected job data. Prompting/generation rules, ranking behavior and product-specific
workflow logic are intentionally excluded from the public recruiter showcase.
"""
from __future__ import annotations


def build_application_pack(*, user, cv, job) -> dict:
    """Public service contract for application-document generation.

    The private implementation returns a compatibility summary, improvement actions,
    a cover-letter draft, application-email draft and tailored-resume draft while
    keeping generated claims grounded in candidate-provided evidence.
    """
    raise NotImplementedError(
        "The full JobHunt MU Application Studio implementation is private. "
        "See README.md for the demonstrated workflow and repository boundaries."
    )
