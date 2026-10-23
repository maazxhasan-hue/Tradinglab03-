# File Upload Security Audit Playbook

## Goal

Identify every user-controlled file-upload path in `maazxhasan-hue/Tradinglab03-`, verify type/size/content validation, isolated storage, non-execution, access control, and safe error handling; fix confirmed defects; add regression tests; and report evidence without overstating coverage.

## Scope and current baseline

Review frontend forms, backend routes, workers, temporary-file handling, storage providers, file parsers, archive extraction, downloads, and relevant third-party integrations.

Prior review found no user-controlled binary upload endpoint in the code reviewed. The project builder instead accepts structured JSON/text, validates generated paths, limits generated manifests to 30 files and generated text to 1.5 MB, stores ZIP archives in the database, and does not execute generated code in the reviewed API. Treat this as a scoped prior finding, not a guarantee about all code, services, or deployed configuration. Re-scan after relevant changes.

## Ordered workflow

1. **Discover:** Search for file inputs, multipart requests, upload handlers, file-processing libraries, temporary files, object-storage writes, archive extraction, and upload integrations.
2. **Trace and classify:** Follow each candidate from UI/request through validation, processing, storage, retrieval, and deletion. Distinguish binary uploads from ordinary forms, pasted text, and application-generated archives.
3. **Validate type:** Use a strict allowlist. Check extension, declared MIME type, and actual signature or safely parsed content as appropriate; never trust client-supplied metadata alone.
4. **Validate size and content:** Enforce request/file limits before expensive processing. Reject malformed or unsupported content. For archives, cap expanded size, entry count, nesting, and processing time; guard against path traversal and decompression bombs.
5. **Isolate storage:** Keep files outside the public web root or in isolated object storage. Use generated storage keys, restrict access, prevent path traversal, and ensure untrusted files cannot overwrite application files.
6. **Prevent execution:** Never execute, import, evaluate, or dynamically load uploaded content as application code. Configure storage and serving paths as non-executable. Sandbox any necessary processing.
7. **Verify access and delivery:** Check authentication, per-object authorization, safe download headers, content-type handling, and prevention of cross-user access.
8. **Harden errors and logs:** Return generic client-safe errors; keep diagnostic details server-side. Never log secrets or unnecessarily sensitive file contents.
9. **Fix and test:** Make minimal targeted changes. Add regression tests for allowed and rejected formats, size boundaries, malformed files, path traversal, archive abuse, access control, and execution attempts where applicable.
10. **Verify and report:** Review the diff, run relevant tests/security checks, inspect CI and deployment smoke results separately, and complete the audit report with limitations.

## Non-negotiable rules

- Treat filenames, extensions, MIME headers, and file bytes as untrusted.
- Fail closed on invalid, unsupported, oversized, or ambiguous input.
- Do not place untrusted files in publicly writable or executable locations.
- Never execute uploaded content as application code.
- Do not expose stack traces, internal paths, secrets, or raw database errors to users.
- Log useful diagnostics server-side without leaking secrets or sensitive file content.
- Make the smallest safe changes; avoid unrelated refactors.
- Do not claim security based only on a search result or a passing test.
- Distinguish code review, tests, CI, merge, and production deployment as separate evidence levels.
- **Toolbox rule:** Save every artifact made for this audit—documents, templates, approved scripts, test fixtures, and checklists—under `toolbox/file-upload-security/`. Add a link and purpose for every artifact to this playbook and update the folder README in the same change. See [README](./README.md), [upload inventory template](./templates/upload-inventory.md), [audit report template](./templates/audit-report.md), and [test matrix template](./templates/test-matrix.md). Do not store secrets, real customer files, or production uploads here. Scripts are not approved until reviewed, narrowly scoped, safe to run, and documented.

## Artifact index

- [README and toolbox policy](./README.md) — folder purpose, contents, and artifact-storage rule.
- [Upload inventory template](./templates/upload-inventory.md) — record discovered paths and data flow.
- [Audit report template](./templates/audit-report.md) — consistent evidence-based final report.
- [Test matrix template](./templates/test-matrix.md) — test cases and outcomes.

## What done looks like

- Every relevant upload path has been identified and traced, or the report explicitly documents that no upload path was found within the reviewed scope.
- Applicable type, size, and content validation is verified.
- Storage isolation, access control, and non-execution are verified where uploads exist.
- Abuse-case regression tests and relevant existing checks pass.
- Findings, fixes, evidence, deployment status, and limitations are documented.
- Final status is one of `PASS`, `PASS WITH LIMITATIONS`, or `FAIL`.

## Completion checklist (check before closing the task)

Mark each item only when supported by evidence. Use **N/A with a reason** when a control does not apply; use **Not verified** when evidence is missing.

- [ ] **Scope is recorded:** repository, branch/commit, directories, routes, workers, storage providers, and relevant external integrations reviewed are listed.
- [ ] **Upload discovery is evidenced:** search terms/locations and results are recorded; any “no upload endpoint found” conclusion is explicitly limited to the reviewed scope.
- [ ] **Data flows are traced:** each discovered candidate is followed from entry point through validation, processing, storage, retrieval, and deletion.
- [ ] **File type is validated:** allowlist and extension/MIME/signature or parser checks are verified, as appropriate; client metadata is not trusted alone.
- [ ] **Size and content are bounded:** request/file limits, malformed-content handling, and archive expansion/entry/nesting/time limits are verified where applicable.
- [ ] **Storage is isolated:** files cannot be written into the web root or overwrite application files; access is restricted and path traversal is prevented.
- [ ] **Execution is prevented:** untrusted content is not executed, imported, evaluated, or served in an executable context; any processing is appropriately sandboxed.
- [ ] **Access and delivery are checked:** authentication, object-level authorization, cross-user access, and download/content headers are tested where applicable.
- [ ] **Errors and logs are safe:** clients receive generic errors; server logs retain useful diagnostics without exposing secrets or sensitive contents.
- [ ] **Regression tests are recorded:** applicable positive and negative cases are run; non-applicable cases have a reason; results and commands/evidence are attached.
- [ ] **Changes are reviewed:** the diff is minimal, relevant tests/security checks pass, and no unrelated changes or secrets are included.
- [ ] **CI and deployment are distinguished:** CI results, merge status, and production smoke tests are each recorded separately; unrun checks are not represented as passing.
- [ ] **Toolbox is current:** every artifact created for this task is saved under `toolbox/file-upload-security/`, linked from this playbook, and listed in [README.md](./README.md). No secrets, production uploads, or real customer files are stored there.
- [ ] **Final report is complete:** findings, severity, evidence, fixes, residual risks, and a justified final status are documented using the [audit report template](./templates/audit-report.md).

**Close-out rule:** Do not mark the task fully complete while a required applicable item is unchecked, a material finding remains, or a critical verification is missing. If scope or deployment cannot be fully verified, report **PASS WITH LIMITATIONS** only when the evidence supports it; otherwise report **FAIL** or **Not yet complete**.

## Required final report fields

1. Scope reviewed.
2. Upload inventory (or qualified no-upload finding).
3. Findings with severity, impact, and evidence.
4. Changes made and PR/commit references.
5. Verification results, with tests/CI/deployment distinguished.
6. Remaining risks and unverified areas.
7. Final status.
