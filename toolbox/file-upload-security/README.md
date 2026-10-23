# File Upload Security Toolbox

This folder is the source of truth for the File Upload Security Audit Playbook and its reusable audit artifacts.

## Contents

- [Playbook](./PLAYBOOK.md) — goal, ordered workflow, rules, evidence requirements, and completion criteria.
- [Upload inventory template](./templates/upload-inventory.md) — record each upload path and trace its data flow.
- [Audit report template](./templates/audit-report.md) — record scope, findings, evidence, fixes, verification, and residual risks.
- [Test matrix template](./templates/test-matrix.md) — track security test cases and results.

## Toolbox rule

For every future artifact created for this task—including documents, templates, approved scripts, test fixtures, or checklists—save it under `toolbox/file-upload-security/`. Update [PLAYBOOK.md](./PLAYBOOK.md) in the same change with a link and a one-line purpose. Do not store secrets, production uploads, personal data, or real customer files here. Scripts must be reviewed, narrowly scoped, safe to run, and documented before being marked approved.

## Current audit context

The prior code review did not identify a user-controlled binary file-upload endpoint in the code reviewed. It did identify a project builder that generates text files and ZIP archives, stores archives in the database, and does not execute generated code in the reviewed API. This is a scoped finding, not proof about every deployment or external integration. Re-run the discovery steps whenever the codebase or integrations change.
