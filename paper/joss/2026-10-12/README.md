# JOSS draft received 12 October 2026

- [Supplied Markdown](paper.md) and [supplied bibliography](paper.bib), unchanged.
- [Collaborator Word copy](cubedynamics-joss-collaborator-draft.docx), suitable
  for uploading to Google Docs. Prose and section order are retained; citation
  keys become 14 numbered references in first-use order.
- [Conversion script](build_docx.py), requiring `python-docx`. After rebuilding,
  apply the documents skill's Google Docs title sanitizer and render for review.
- [Documentation content map](../../../docs/documentation/manuscript_content_map.md).

The missing `figures/figure1_order_semantics.png` was recovered by rendering and
cropping the supplied main manuscript's Figure 1 on PDF page 2. It is a supplied
conceptual figure, not new observational evidence. The original PDF remains
unchanged. The Word file includes the figure and its Markdown caption.

The Word copy was sanitized for Google Docs title borders and all five rendered
pages inspected. No Google Docs upload or collaborator messages were sent.
The original Markdown remains the source for submission; language edits in
Google Docs will need deliberate reconciliation into it.

## Items for collaborator and author review

These are observations about the supplied draft, not instructions to change
software, publish, or submit anything.

- The draft contains pre-submission directions within the prose, including
  release instruction synchronization, archival requirements, funding, and
  author verification. Decide how to resolve these before the final submission.
- The AI disclosure describes an earlier environment as GPT-5. This conversion
  session identifies as GPT-6; confirm the disclosure across all sessions.
- The main PDF says retained claims were human reviewed; the JOSS text says
  final human review has not occurred. Confirm the intended scope and wording.
- The Working Lands fixture exists in this repository, but a complete frozen
  submission bundle joining fixture, output map, serialized branch records,
  tests, dependencies, and revision is a separate requirement. The draft's
  missing-archive wording should distinguish those states.
- README installation text currently foregrounds rc1 while the draft cites
  rc3. This intake preserves that discrepancy as a review item; it does not
  independently verify published artifact contents or alter release guidance.
- All 14 citation keys resolve to the supplied bibliography. This is citation
  resolution, not a fresh literature audit or JOSS-format compliance review.

The full main/SI bibliographies remain in the retained PDFs; the supplied
JOSS bibliography does not cover every reference in those longer documents.
