# Outbound material filenames

App storage names, download names, cache paths, and upload-returned names are internal implementation details. They may contain prefixes, numeric IDs, timestamps, hashes, UUIDs, or storage keys. Do not require the App to rename them and do not modify App records merely to clean a filename.

The invariant applies at the external submission boundary: every resume or Cover Letter shown to an employer must have a clean, human-readable basename.

## Prepare outbound copies

Immediately before attaching files to an ATS or webmail message:

1. Resolve the exact material content and extension from the selected App slot, saved Cover Letter, or tailored-material manifest.
2. Create a local outbound copy in the current pulse workspace. Do not rename or overwrite the App cache/source file.
3. Choose the clean basename from logical material metadata, never from the raw storage/download basename:
   - existing resume: use the user-visible original resume name when available; otherwise use `<Candidate Name> - CV.<ext>`;
   - tailored resume: use `<Candidate Name> - CV - <Company>.<ext>`;
   - Cover Letter: use `<Candidate Name> - Cover Letter - <Company>.<ext>`.
4. Remove characters that the local filesystem or ATS rejects, collapse repeated whitespace or separators, and retain the correct extension. Do not include a leading ID, hash, UUID, timestamp, database key, download token, or App storage prefix.
5. Verify the outbound copy exists and contains the same bytes as the selected material. Record its exact basename for reconciliation.

If a saved logical filename is already clean, preserve it. Do not guess that an arbitrary leading word or number is a storage prefix and truncate it; when clean metadata is unavailable, use the fallback pattern above.

## Verify in the external UI

After an ATS or webmail UI accepts the file, inspect the displayed attachment name before submission or sending.

- It must exactly match the prepared outbound basename.
- If the UI displays a dirty internal name, remove that attachment and upload the clean outbound copy again.
- Do not submit or send while a resume or Cover Letter still exposes an App storage prefix.

This rule applies equally to standard materials, locally generated materials, and materials that were generated locally, uploaded to the App, downloaded again, and later submitted.
