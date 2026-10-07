---
name: jobfishing-tailor
description: Create a truthful tailored CV and Cover Letter for one jobfishing job using multi-stage review, local LaTeX PDF rendering, verification, and final App upload. Use only when the user explicitly asks for tailored or customized application materials. Do not invoke for ordinary applications that use an existing resume and DOCX Cover Letter.
---

# jobfishing Tailor

Run only after an explicit tailored-material request. Explicit invocation is the feature gate; do not look for an App-side enablement flag. Read, upload, and verify jobfishing data only through its MCP tools; never operate the App frontend in a browser.

This Skill always produces a pair: one tailored CV and one tailored Cover Letter. It does not mean “CV only.” A standard application that keeps an existing App resume belongs directly to `$jobfishing-apply` and must not invoke this Skill.

## Check the shared environment

First run the quick doctor from `$jobfishing-materials-setup`:

```text
python ../jobfishing-materials-setup/scripts/materials_doctor.py
```

Resolve the path from this skill directory. If `ready=true`, retain the absolute `engines.lualatex.path` and `engines.xelatex.path` returned by doctor and use those exact executables for this run. Do not assume the current host's shell `PATH` matches the host that configured LaTeX. If doctor is not ready, use `$jobfishing-materials-setup` to verify or repair the shared system environment. Obtain approval before any system installation, then resume this same tailoring request after doctor passes.

## Establish facts and workspace

1. Identify exactly one jobfishing job and one base resume.
2. Ask once for confirmation that Basic Info, Experience, and the base resume are current if the user has not already confirmed in this task.
3. Read the current Basic Info, Experience, saved answers, complete JD, match details, and base resume.
4. Create a local workspace under `jobfishing-materials/<company>-<role>-<job_id>/` for sources, reviews, rendered pages, verification, and the final manifest.
5. Read the shared [Cover Letter quality workflow](../jobfishing-apply/references/cover-letter-quality.md). Build one evidence plan used by both materials.

## Job facts to tailor against

`get_job_detail` returns `requirements` with each skill marked required or preferred, the core work, seniority and minimum years, plus the company description and `contact`. Tailor to the required skills first and the core work second; use the company description only for genuine, checkable context. Do not claim a preferred skill the sources do not support.

## Draft and review with separate roles

When the host supports subagents, use bounded parallelism:

- CV Drafter: tailor structure and bullets from verified facts.
- Cover Letter Drafter: produce the final body using the shared evidence plan.
- Truth Reviewer: check all claims, dates, metrics, titles, contact fields, and gap language against sources.
- Relevance Reviewer: check JD coverage, prioritization, repetition between CV and letter, and unsupported keyword use.

The orchestrating Agent owns revisions and final decisions. Give reviewers drafts and the evidence plan inline so they do not independently invent context. If subagents are unavailable, execute the same roles as distinct passes.

Never create a skill, date, number, employer, responsibility, or scope claim. Reorder, compress, and rewrite only what the sources support.

## Render both tailored PDFs

Copy the selected templates from the shared jobfishing materials environment or use a user template that has passed its smoke test.

- Compile the CV with the absolute LuaLaTeX path returned by doctor.
- Compile the Cover Letter with the absolute XeLaTeX path returned by doctor.
- Always use `-no-shell-escape`, `-interaction=nonstopmode`, and `-halt-on-error` in an isolated material directory.
- Keep editable `.tex` sources and all intermediate artifacts local.

Inspect every rendered page for clipping, overlaps, orphaned headings, unexpected blank pages, signature visibility, font consistency, and readable hierarchy. Verify extractable text, reading order, contact details, key evidence, and honest JD keyword coverage.

Apply at most two targeted render/review revisions. If the PDFs still fail, show the concrete failure and stop instead of weakening facts or looping indefinitely.

## Save and hand off

1. Upload the final Cover Letter PDF with `upload_tailored_cover_letter`; the App will use the job's latest Cover Letter at mark time.
2. Upload only the final CV PDF with `upload_tailored_resume`; the returned resume choice must be the App's existing `tailored` value.
3. Confirm the App now shows both the tailored CV and Cover Letter as the job's current materials.
4. Do not upload LaTeX, reviews, logs, or rendered-page images.
5. Read [materials-manifest.md](references/materials-manifest.md) and write `materials-manifest.json` only after both current materials are saved in the App. Preserve clean employer-facing filenames in the manifest even if the App upload response or a later download uses an opaque storage basename.
6. Show a compact change and verification summary.

Do not submit the application or call `mark_applied` inside this Skill. After the two files are verified and uploaded, hand the job back to `$jobfishing-apply`. If the user asked for “tailor and then apply” in the same task, continue with `$jobfishing-apply` after showing the completed material summary; final-submit authorization still follows the ordinary application rules. `$jobfishing-apply` consumes the clean local PDF paths and uses the existing `resume_choice="tailored"`, then runs the browser submission workflow. If the files must be downloaded from the App again, it recreates clean outbound copies rather than attaching opaque App download names. The App snapshots the current Cover Letter automatically at mark time.

If the App has not yet exposed a required upload/revision capability, preserve the verified local files, name the exact missing MCP capability, and stop before the submission workflow. Do not substitute an untracked material reference.
