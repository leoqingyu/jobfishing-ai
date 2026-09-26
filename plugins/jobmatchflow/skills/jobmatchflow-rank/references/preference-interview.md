# Preference interview and personalized ranking

## Persistent location

Save the confirmed profile as one Experience Agent Q&A entry:

```text
key: job_ranking_preferences_v1
value: <canonical preference profile>
```

This is the Agent-maintained ranking profile. The user's separate `scoring_preferences` field is additional source material and must not be overwritten. If the two conflict, show the conflict and ask which rule should govern this workflow; record the resolved rule in the Agent Q&A profile while leaving the user field untouched.

## Multi-turn interview

Reuse facts already present in Basic Info and Experience. Do not make the user repeat employment history, technologies, location, or work authorization unless a preference differs from the factual profile or needs clarification.

Ask two to four focused questions per turn. Adapt the next round to prior answers rather than dumping a fixed questionnaire.

Cover these decision areas before saving:

1. **Target direction** — desired functions and work content, acceptable adjacent functions, seniority range, industries or company types.
2. **Hard constraints** — authorization, countries/locations, remote/hybrid/on-site rules, commute/relocation, required employment type, language, schedule/travel, salary floor when the user wants it enforced.
3. **Work preferences** — responsibilities that energize or drain, skills they want to use or grow, ownership/leadership balance, culture and management preferences.
4. **Trade-offs** — what may compensate for a weaker factor, which rules are absolute, appetite for stretch roles, capability fit versus career direction.
5. **Curation policy** — minimum App score or accepted App decision, whether flagged jobs require review, maximum jobs to add per run, and quality-versus-volume preference.

Do not force a user to specify salary, industry, company size, or any other optional preference they do not care about. Mark it `no preference` instead of inventing one.

After each round, summarize what changed and name unresolved choices. Continue until no decision-critical ambiguity remains.

## Canonical profile

Before saving, show one compact profile with this structure:

```markdown
# Job Ranking Preferences v1
Last confirmed: YYYY-MM-DD

## Target direction
- Target functions:
- Acceptable adjacent functions:
- Seniority:
- Industries/company types:

## Hard constraints
- Work authorization/geography:
- Location/remote/commute/relocation:
- Employment type/schedule/travel:
- Languages:
- Compensation:
- Other vetoes:

## Work and growth preferences
- Prefer:
- Avoid:
- Skills to use:
- Skills to grow:
- Culture/management:

## Trade-offs
- Absolute rules:
- Acceptable compromises:
- Stretch-role tolerance:

## Curation policy
- Minimum App score/decision:
- Handling of hard-standard or uncertainty flags:
- Maximum additions per run:
- Quality-versus-volume:
```

Omit irrelevant bullets, but keep the headings so later Agents can locate the rules. Ask the user to approve or correct this exact profile. Call `save_agent_answer` only after approval.

## Subsequent invocations

Do not repeat the full interview automatically. Show a short digest of the saved profile and ask:

> Are these job filtering preferences still valid? Do you want to adjust the target direction, hard constraints, trade-off rules, minimum score, or the number added to Saved this round?

If unchanged, proceed. If changed, ask only the follow-up questions needed for the affected sections, show the complete revised profile, obtain approval, and save the same key again.

## Available ranking evidence

`list_jobs` (paged) can provide the App score and decision, `list_group` (1 Best, 2 Good, 3 Partial) and `intent` (the App's AI verdict: `fit`, `want`, `good[]`, `watch_out[]`; null for free users and for users who have not done the App's preference interview), job seniority, source, country and location, `remote_mode`, `employment_type`, `required_languages`, `required_degree`, `salary` (possibly an estimate), `visa_sponsorship_offered` and `work_permit_required`, `company_info` (industry, size, website, LinkedIn), `contact`, and whether the job is already dismissed (Not for me), Saved, or in an application.

`get_job_detail` can provide the cleaned/raw full JD, `requirements` (each skill marked required or preferred, the core work, seniority and minimum years), the company description, the hard constraints, and for older scores requirement matches with text, category, importance, match level, reason and confidence.

Use these as follows:

- App score/decision is the existing capability-match baseline; when `intent` is present, the App's fit/want verdict is part of that baseline. Do not recreate either with fixed universal weights.
- The App's hard-standard verdict no longer checks language or work authorization (those two are always true now); check `required_languages`, `visa_sponsorship_offered` and `work_permit_required` yourself against the user's profile. User hard vetoes and any hard conflict you find exclude automatic Saved regardless of score.
- Full JD and requirement matches explain whether the job satisfies the user's target direction and preferences.
- Unknown decision-critical conditions become visible questions or flags, never silent passes.
- Job title is only a label. Judge the function and nature of the work.

The public `ai-job-search` framework's useful transferable principles are honest gaps, pre-score hard gates, function-over-title matching, and separating cheap triage from final application evaluation. Its fixed example weights and thresholds are not universal and must not override this user's confirmed profile.

## Decision output

Do not manufacture a second overall match score. Retain:

- App score and decision;
- hard-standard verdict;
- personalized preference fit: `strong`, `acceptable`, `uncertain`, or `conflict`;
- decisive supporting JD evidence;
- action: `prepare`, `review`, `leave`, or `exclude`.

A job is eligible for automatic Saved only when it meets the user's stored App-score/decision rule, passes App and user hard constraints, has enough JD evidence, and has `strong` or `acceptable` preference fit. Respect the user's stored maximum additions per run and use App score as the tiebreaker unless the user specified another priority.
