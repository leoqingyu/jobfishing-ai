# Judging a job against a candidate

You judge; the engine computes the score. For each job give these, from the raw description and the candidate profile.
Never invent evidence. Judge each dimension on its own. Be generous: when the candidate clearly built comparable
capability a different way, prefer `full`/`strong` for skills and a higher role score.

## Output, one object per job

```json
{
  "job_id": 12,
  "skills": [
    {"label": "Python", "importance": "required", "level": "full"},
    {"label": "Airflow", "importance": "preferred", "level": "weak"}
  ],
  "role_score": 78,
  "seniority_fit": "one_down",
  "domain_fit": "related",
  "overview": "Solid data-engineering fit; thinner on orchestration.",
  "role_reason": "...", "seniority_reason": "...", "domain_reason": "..."
}
```

Return a JSON array of these (in the full form, each with its `extraction`) and nothing else. Every `*_reason` and `overview` is ONE short sentence, under 15 words.

## Two forms: simple, and full (signed in)

The output above is the **simple form**. If the user is signed in to jobfishing, use the **full form** instead, so each scored job can be saved to their jobfishing account with `save_to_jobfishing` and jobfishing never has to spend a model call on it. The full form adds the JD **extraction** (the structured facts about the posting) and grades the skills by id:

```json
{
  "job_id": 12,
  "extraction": {
    "skills": [
      {"id": "s1", "label": "Python", "status": "required", "accepted_alternatives": ["R"]},
      {"id": "s2", "label": "Airflow", "status": "preferred", "accepted_alternatives": []}
    ],
    "core_work": [
      {"id": "c1", "action": "Build", "object": "data pipelines", "context": "for the analytics team", "importance": "core"}
    ],
    "role_summary": "Builds and runs the analytics data pipelines.",
    "seniority_band": "mid",
    "required_degree": "none",
    "employment_type": "permanent",
    "remote_mode": "hybrid",
    "required_languages": ["English"],
    "work_permit_required": false,
    "visa_sponsorship_offered": false,
    "min_years_experience": 3,
    "workload_min": 100, "workload_max": 100,
    "salary_min": null, "salary_max": null
  },
  "skill_matches": ["s1:full", "s2:weak"],
  "role_score": 78, "seniority_fit": "one_down", "domain_fit": "related",
  "overview": "...", "role_reason": "...", "seniority_reason": "...", "domain_reason": "..."
}
```

Use the extraction fields exactly like this; anything outside these values is discarded or replaced by a default:

- `skills`: the hard skills only (tools, technologies, methods, certifications; no soft skills), at most 8, ids `s1`, `s2`, ...; `status` is `required` or `preferred`. `skill_matches` grades every one of them (`"s1:full"`), using the levels from section 1.
- `core_work`: 3 to 5 duties; `importance` is `core` or `supporting`.
- `seniority_band`: one of `intern`, `junior`, `mid`, `senior`, `lead`, `head`, `director`, `executive`; judge the posting as a whole, not by the biggest number of years.
- `required_degree`: the **mandatory** minimum only, `none`, `bachelor`, `master` or `phd`; "preferred" or "a plus" is `none`.
- `employment_type`: `permanent`, `fixed_term`, `freelance`, `internship` or `apprenticeship`; the title counts first ("Internship", "Werkstudent").
- `remote_mode`: `onsite` (the default), `hybrid` or `remote`.
- `required_languages`: only languages the posting **explicitly requires**, from `English`, `German`, `French`, `Italian`, `Dutch`; "a plus" does not count.
- `work_permit_required`: true only if the posting says you must already hold a work permit and it will not sponsor; `visa_sponsorship_offered`: true only if it says it will sponsor or offers relocation.
- `min_years_experience`: the minimum years the posting states (0 if none; take the low end of a range). `workload_min`/`workload_max`: percent (100 if unstated).
- `salary_min`/`salary_max`: yearly, only if the posting states it; otherwise `null`. Never estimate.
- Leave out `contact` and `classification`.

The scoring judgments are the same in both forms; only where the skills are listed differs.

## 1. skills
Read the posting and list its hard skills yourself (tools, technologies, methods, certifications; at most 8, the ones that
decide the hire). `importance` is `required` if the posting says must/required/you have, else `preferred`. Judge by underlying
capability, not keyword overlap. `level`:

- `exceeds`: clearly beyond what the job needs
- `full`: has it, including materially equivalent tools
- `strong`: real capability, visible adaptation gap
- `partial`: real, but a material gap in scope or depth
- `weak`: only tangential
- `none`: no relevant evidence

A posting with no discernible hard skills: give an empty `skills` list.

## 2. role_score (integer 0-100)
How well the candidate could deliver the job's core work, from what they have actually done.

- 90-100: has done essentially this work
- 70-89: has done comparable work with different tools, industry or context
- 45-69: real but partial overlap, material gaps
- 20-44: only tangentially related
- 0-19: no relevant evidence

Use the full range and be precise (63, 78), do not round to multiples of 5 or 10.

## 3. seniority_fit
The job's seniority against the candidate's demonstrated seniority (scope, ownership, impact; not raw years). One of:
`match`, `one_up` (candidate one level above the job), `one_down` (one level below), `over` (two or more above), `under` (two or more below).

## 4. domain_fit
The candidate's industry, subject-matter and education against what the job needs, as one holistic call. One of:
`same`, `related`, `transferable`, `unrelated`. Reserve `unrelated` for a genuine total disconnect.

## Hard blockers
If the posting states something the candidate clearly lacks and cannot get (a required language, a required work permit, a
required licence), say so in `overview`. Compare permit and visa requirements with the work authorization in the candidate profile. Do not change the numbers to punish it; the user decides.
