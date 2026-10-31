# Prospect review & proposal draft — MCQ PDF to Excel automation

**Prepared:** 2026-10-17  
**Status:** Draft only — not sent. The source post appears approximately one month old, so re-check whether the requester still needs help before any contact.  
**Source:** https://www.reddit.com/r/Excel247/comments/1we5tr2/looking_for_a_reliable_solution_to_convert_mcq/  
**Source evidence:** The author asks for a workflow to convert large MCQ PDFs (Gujarati and English text, mathematical expressions, diagrams/images) into a fixed 24-column Excel structure, preserving wording and associating extracted images with the correct questions/options. The post says a sample PDF and Excel template can be provided.  
**Fit:** Potentially relevant to document automation / Python workflow services.  
**Confidence:** Medium — genuine buyer intent is expressed in the post, but current status, budget, technical acceptance criteria, and the author's identity/eligibility are not independently verified.  
**Important limitation:** Do not promise perfect OCR or exact preservation until a representative sample has been tested. Gujarati text, equations, scans, and image-to-question mapping require validation and may need manual review.

## Tailored reply draft (do not send automatically)

Hi — I came across your post about converting MCQ PDFs into your 24-column Excel format while preserving Gujarati/English wording, mathematical expressions, and question/option images.

A sensible first step would be a small proof of concept using one representative PDF and your Excel template. I’d test text extraction, image extraction/mapping, and the final column structure, then report which cases can be automated reliably and which need a review queue. I wouldn’t promise zero text changes until the sample passes comparison checks.

If you’re still looking, could you share a small sample PDF (with any sensitive details removed) and the blank Excel template, and confirm whether the PDFs are searchable or scanned? That would let us define a realistic test and acceptance checklist before discussing price or timeline.

Portfolio: https://maazxhasan-hue.github.io/Tradinglab03-/dashboard/website.html

## Proposed phased scope — for discussion only

1. **Discovery sample:** inspect one representative PDF and the blank template; classify searchable text, scanned pages, tables, equations, and image cases.
2. **Proof of concept:** extract a limited sample into the exact requested columns; export referenced images with stable filenames and a mapping manifest.
3. **Validation:** compare extracted text against source pages, flag low-confidence OCR and ambiguous image associations, and generate a QA report instead of silently guessing.
4. **Batch workflow (only after sample approval):** process multiple PDFs, produce the Excel output plus image folder/manifest, and log errors for manual review.

## Acceptance criteria to agree with the requester

- Output columns and order match the supplied 24-column template.
- Original question and option text is not intentionally rewritten; uncertain OCR is flagged for review.
- Image filenames are unique and mapped to the correct question/option with a traceable manifest.
- Sample output is checked against source pages, including Gujarati, numerals, equations, and image-heavy pages.
- Unsupported or ambiguous cases are reported explicitly; no guarantee of perfect extraction is made before testing.
- Client confirms the sample output before any larger batch is started.

## Questions before quoting

- Are PDFs text-searchable, scanned, or mixed?
- Can they provide a representative sample plus the blank template?
- How many PDFs and total pages are expected per batch?
- Are answers/explanations already present in the PDF, or must they be supplied separately?
- Should images be embedded in Excel or referenced by filenames?
- What accuracy threshold and manual-review process will they accept?
- What budget, deadline, and data-handling/privacy constraints apply?

## Qualification / safety checks

- [ ] Re-open the source post and verify that the request is still active.
- [ ] Check the community rules before responding; no unsolicited repeated messages.
- [ ] Do not request or store sensitive exam materials unnecessarily; use a redacted/sample file first.
- [ ] Agree scope, price, timeline, ownership, and payment milestones in writing before implementation.
- [ ] Do not claim previous client work or guaranteed accuracy that has not been demonstrated.
- [ ] No message, bid, contract, payment, or deployment has been made by preparing this draft.
