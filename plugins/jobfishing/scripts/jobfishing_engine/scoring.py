"""Turn a model's four judgments into the same 0-100 score the jobfishing app shows.

The model only judges; this module does the arithmetic, so the number is identical whichever agent or model judged and
comparable with the app's own scores. Weights and thresholds mirror the app's pipeline.
"""

from __future__ import annotations

SKILL_VALUE = {"exceeds": 1.0, "full": 0.9, "strong": 0.75, "partial": 0.5, "weak": 0.25, "none": 0.0}
SKILL_WEIGHT = {"required": 3, "preferred": 1}
SENIORITY_VALUE = {"match": 100, "one_up": 85, "one_down": 70, "over": 40, "under": 30}
DOMAIN_VALUE = {"same": 100, "related": 80, "transferable": 60, "unrelated": 30}
DIMENSION_WEIGHT = {"qualification": 0.30, "role": 0.40, "seniority": 0.15, "domain": 0.15}
NO_SKILLS_QUALIFICATION = 60.0
GENERATE_AT = 80
REVIEW_AT = 60


def qualification(skills: list[dict]) -> float:
    """Weighted mean of skill levels x 100; required counts 3, preferred 1; an unknown level counts as none."""
    total = weight_sum = 0.0
    for s in skills or []:
        w = SKILL_WEIGHT.get(str(s.get("importance", "required")).lower(), SKILL_WEIGHT["required"])
        total += SKILL_VALUE.get(str(s.get("level", "none")).lower(), 0.0) * w
        weight_sum += w
    return NO_SKILLS_QUALIFICATION if weight_sum == 0 else total / weight_sum * 100


def aggregate(judgment: dict) -> dict:
    """judgment: {skills:[{importance,level}], role_score, seniority_fit, domain_fit}. A missing dimension drops out and the
    others are renormalised; nothing is invented and nothing is capped."""
    dims: dict[str, float] = {"qualification": qualification(judgment.get("skills") or [])}
    rs = judgment.get("role_score")
    if isinstance(rs, (int, float)) and not isinstance(rs, bool):
        dims["role"] = float(min(100, max(0, rs)))
    sen = SENIORITY_VALUE.get(str(judgment.get("seniority_fit", "")).lower())
    if sen is not None:
        dims["seniority"] = float(sen)
    dom = DOMAIN_VALUE.get(str(judgment.get("domain_fit", "")).lower())
    if dom is not None:
        dims["domain"] = float(dom)
    wsum = sum(DIMENSION_WEIGHT[k] for k in dims)
    total = sum(dims[k] * DIMENSION_WEIGHT[k] for k in dims) / wsum
    decision = "generate" if total >= GENERATE_AT else "review" if total >= REVIEW_AT else "discard"
    return {**{k: round(v, 1) for k, v in dims.items()}, "total": round(total, 1), "decision": decision}
