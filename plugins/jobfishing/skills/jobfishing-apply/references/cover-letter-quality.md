# Shared Cover Letter quality workflow

Use this workflow for every jobfishing Cover Letter. Standard DOCX and tailored LaTeX output have identical content-quality requirements; only their renderer differs.

## Evidence plan

Extract the three to five requirements that most influence selection. For each requirement, record:

- the exact verified candidate evidence;
- the source of that evidence in Basic Info, Experience, saved answers, or the selected/submitted resume;
- whether it is direct evidence or a transferable-skill bridge;
- the one point the Cover Letter should communicate.

Leave unsupported requirements visible as gaps. Never add a keyword in a way that implies experience the user does not have.

## Draft and review

Use a drafter pass to produce a company- and role-specific letter from the evidence plan. When the host supports isolated subagents, dispatch a fresh reviewer with the evidence plan and draft inline; the reviewer does not need to reread the entire profile.

The reviewer checks:

1. every factual claim against its cited candidate source;
2. coverage of the highest-value JD requirements;
3. company and role specificity;
4. honest treatment of gaps;
5. duplicated evidence between paragraphs and the resume;
6. concise, human tone and appropriate length;
7. consistency with the selected resume.

The orchestrating Agent owns the final revision. Do not let a reviewer introduce new candidate facts. If isolated subagents are unavailable, run the same rubric as a separate review pass before finalizing.

## Final content contract

- Use the final reviewed paragraphs as the single content source for the attachment, ATS text field, or email body.
- Standard applications use the host's document capability—or the bundled `python-docx` dependency—to render a clean DOCX locally, verify the visible and extracted text, and upload that exact file through `upload_tailored_cover_letter`. Do not call `save_cover_letter_content`, use the App DOCX renderer, or open the jobfishing frontend to upload or download it.
- Keep the verified local DOCX for the current application pulse and submit that same file to the employer. Download it again through MCP only when resuming without the original local file.
- `$jobfishing-tailor` uses the same final content in the selected LaTeX Cover Letter template and compiles it with `xelatex`.
- A rendered file is not ready until its visible text and extracted text agree with the final reviewed paragraphs.
