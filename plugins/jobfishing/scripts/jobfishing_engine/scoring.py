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
    # rounded to one decimal before it enters the total, exactly as the jobfishing app does (ai/scoring_v2.aggregate_match_values)
    return NO_SKILLS_QUALIFICATION if weight_sum == 0 else round(max(0.0, min(100.0, total / weight_sum * 100)), 1)


def skills_of(judgment: dict) -> list[dict]:
    """The skill list for qualification(), from either shape an agent may send:
    the simple one, `skills: [{importance, level}]`, or the full one used for saving to jobfishing, where the JD extraction
    lists the skills with ids (`extraction.skills`) and `skill_matches: ["s1:full", ...]` grades them."""
    ext = judgment.get("extraction")
    listed = ext.get("skills") if isinstance(ext, dict) else None
    matches = judgment.get("skill_matches")
    if isinstance(listed, list) and listed and matches is not None:
        levels = {}
        for m in matches if isinstance(matches, list) else []:
            if isinstance(m, str) and ":" in m:
                sid, level = m.rsplit(":", 1)
                levels[sid.strip()] = level.strip().lower()
        out = []
        for i, sk in enumerate(listed):
            if isinstance(sk, dict) and sk.get("label"):
                out.append({"importance": "required" if sk.get("status") == "required" else "preferred",
                            "level": levels.get(str(sk.get("id") or f"s{i + 1}"), "none")})
        return out
    return judgment.get("skills") or []


def aggregate(judgment: dict) -> dict:
    """judgment: {skills:[{importance,level}], role_score, seniority_fit, domain_fit}. A missing dimension drops out and the
    others are renormalised; nothing is invented and nothing is capped."""
    dims: dict[str, float] = {"qualification": qualification(skills_of(judgment))}
    # A dimension that is absent drops out and the rest are renormalised; one that is present but unusable counts as 0, the same
    # as the jobfishing app does, so a sloppy judgment scores the same here as after it is saved there.
    if judgment.get("role_score") is not None:
        rs = judgment["role_score"]
        dims["role"] = float(min(100, max(0, rs))) if isinstance(rs, (int, float)) and not isinstance(rs, bool) else 0.0
    if judgment.get("seniority_fit") is not None:
        dims["seniority"] = float(SENIORITY_VALUE.get(str(judgment["seniority_fit"]).lower(), 0))
    if judgment.get("domain_fit") is not None:
        dims["domain"] = float(DOMAIN_VALUE.get(str(judgment["domain_fit"]).lower(), 0))
    wsum = sum(DIMENSION_WEIGHT[k] for k in dims)
    total = sum(dims[k] * DIMENSION_WEIGHT[k] for k in dims) / wsum
    decision = "generate" if total >= GENERATE_AT else "review" if total >= REVIEW_AT else "discard"
    return {**{k: round(v, 1) for k, v in dims.items()}, "total": round(total, 1), "decision": decision}
