---
name: jobmatchflow-insights
description: Analyze a user's JobMatchFlow application funnel, stage timing, targeting patterns, and observed outcomes from existing App data. Use only when the user explicitly asks for outcome analysis, funnel analysis, or strategy calibration. Do not invoke during ordinary application or inbox workflows.
---

# JobMatchFlow Insights

This is a read-only analysis workflow. JobMatchFlow remains the source of truth; do not create another outcome database and do not modify profile, matching rules, or application history. Read JobMatchFlow only through its MCP tools; never operate the App frontend in a browser.

## Gather

1. Read current tracking and jobs from JobMatchFlow. Use existing stage, score, source, resume choice, dates, role family, sector, and location fields when present.
   When the user needs all Application information, use `list_tracking` to enumerate every record and then call `get_application_context` for each `tracking_id`; this is where the submitted CV and Cover Letter snapshot, full JD, score, dates, status, and unified notes are retrieved.
   Use `download_application_material` only when the user needs the actual submitted CV or Cover Letter files rather than their context, metadata, or text.
2. Read recruiter feedback from the unified application notes when available and include it as qualitative evidence. Missing feedback must not block quantitative analysis.
3. State the analysis date, included population, exclusions, and missing fields.

## Use the App's definitions

The App has its own Insights page. Any funnel number you report must be computed exactly the way it is, so the two never disagree. Use `list_tracking` (each row has `status`, `status_history` with timestamps, `applied_at`) and count across all applications since the first one; no window, no minimum.

- **Stages** are Applied, Screening, Interview, Offer, in that order, from the current status: `applied` shows in the App as "No answer", `assessment` as "In review", `interview` as "In progress", then `offer` and `no_offer`, or `rejected`.
- **Applied** = every tracked application.
- **Screening** = everyone still in play: anything that is not `rejected`. An application with no answer yet has not failed, it is waiting, so it counts here. A rejected row that had reached an interview also stays counted.
- **Interview** = ever interviewed: status `interview`, `offer` or `no_offer`, or `interview` anywhere in its history (older rows went interview to rejected).
- **Offer** = status `offer`, or `offer` in its history.
- **Replied** = every application whose status is not `applied`. **Response rate** = replied / applied. **Interview rate** = interviews / applied.
- **Median time to reply** = median, over the rows that have it, of the days from applying to the first status change after `applied`, as the user logged it (it is when they recorded it, not when the company wrote).
- **Two ways to be turned down**: `rejected` before an interview, and `no_offer` after one. After an interview the negative outcome is `no_offer`, never `rejected`. "No reply yet" is neither; it is not evidence against the CV.
- **Where you lose them**: compare the rejected-before-interview share of all applications with the no-offer share of interviews, and say which is worse. A big early loss points at the CV and targeting; a big late loss points at interview preparation.

Then add what the App does not compute (role family, sector, source, match-score band, location, resume choice), suppress or label comparisons on very small groups, and treat every pattern as correlation. Do not claim one resume, keyword or source caused an outcome without an actual experiment.

## Deliver

Give a compact report with:

1. what the data reliably shows;
2. what remains uncertain;
3. targeting choices to continue or stop;
4. one or two bounded experiments for the next application pulse;
5. the metric and sample threshold for evaluating each experiment.

Do not automatically edit Basic Info, Experience, resumes, scoring, jobs, or tracking records.
