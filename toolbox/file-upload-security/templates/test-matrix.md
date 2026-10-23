# File Upload Security Test Matrix

Fill in applicability and evidence for every test. Mark cases **N/A** only when the corresponding upload/processing capability is demonstrably absent from the reviewed scope.

| ID | Test | Expected result | Result | Evidence / notes |
|---|---|---|---|---|
| UPL-01 | Supported file with valid signature and content | Accepted only if allowed by policy | Not run | |
| UPL-02 | Disallowed extension | Rejected | Not run | |
| UPL-03 | Allowed extension with mismatched MIME/signature | Rejected | Not run | |
| UPL-04 | Malformed or truncated file | Rejected safely; no crash or leak | Not run | |
| UPL-05 | File exceeds configured size limit | Rejected before expensive processing | Not run | |
| UPL-06 | Request exceeds body limit | Rejected safely | Not run | |
| UPL-07 | Filename/path traversal payload | Cannot escape isolated storage or overwrite files | Not run | |
| UPL-08 | Archive with excessive entries/expanded size/nesting | Rejected within configured limits | Not run | |
| UPL-09 | Script/executable or active content | Never executed; safely rejected or served as inert download | Not run | |
| UPL-10 | Unauthenticated upload/download | Denied where authentication is required | Not run | |
| UPL-11 | User A requests User B's object | Denied | Not run | |
| UPL-12 | Error during parsing/storage | Generic client response; diagnostic server log | Not run | |
| UPL-13 | Storage and retrieval headers/configuration | Non-public/non-executable and correctly authorized | Not run | |
| UPL-14 | Regression suite after remediation | Relevant tests and checks pass | Not run | |

## Run metadata

- **Commit / PR:**
- **Environment:**
- **Command(s):**
- **CI run:**
- **Reviewer:**
- **Known limitations:**
