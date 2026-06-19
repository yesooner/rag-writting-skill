# Citation Registry Rules

## Registry Record

Use one JSON object per visible cited claim:

```json
{
  "claim_id": "intro_001",
  "manuscript_section": "1 Introduction",
  "source_id": "paper_001",
  "cite_key": "Smith2024Example",
  "card_id": "paper_001_background_003",
  "source_class": "B_background",
  "source_type": "paper",
  "cite_allowed": true,
  "reference_allowed": true,
  "claim": "The cited claim in manuscript wording.",
  "supporting_text": "Source text or card evidence.",
  "source_location": {
    "page_start": null,
    "page_end": null,
    "section": "",
    "clause": "",
    "claim_number": ""
  }
}
```

Do not write internal-only data evidence into `citation_registry.jsonl`. Use `data_evidence_log.jsonl` or `internal_evidence_log.jsonl`.

## Source Metadata

Minimum metadata:

```json
{
  "source_id": "paper_001",
  "cite_key": "Smith2024Example",
  "source_class": "A_core",
  "source_type": "paper",
  "title": "",
  "authors": [],
  "year": null,
  "journal": "",
  "volume": "",
  "issue": "",
  "pages": "",
  "doi": "",
  "publisher": "",
  "place": "",
  "url": "",
  "access_date": "",
  "cite_allowed": true,
  "reference_allowed": true
}
```

Patent metadata:

```json
{
  "source_id": "patent_001",
  "source_type": "patent",
  "title": "",
  "inventors": [],
  "assignee": "",
  "jurisdiction": "",
  "patent_number": "",
  "application_number": "",
  "publication_number": "",
  "filing_date": "",
  "publication_date": "",
  "claims_used": []
}
```

Standard/code metadata:

```json
{
  "source_id": "standard_001",
  "source_type": "standard",
  "standard_number": "",
  "title": "",
  "version_year": "",
  "issuing_body": "",
  "publisher": "",
  "clause": "",
  "clause_title": ""
}
```

## First-Citation Ordering Algorithm

Never trust old numbers in a draft. Reconstruct them.

1. Parse manuscript body and identify visible citation placeholders or citation records.
2. Resolve each occurrence to a stable `source_id` or `cite_key`.
3. Walk occurrences in document order.
4. If the source has not appeared before, assign the next integer.
5. If the source has appeared before, reuse its existing integer.
6. Replace all body citation numbers using the source-to-number map.
7. Generate the final reference list by sorting unique sources by assigned number.
8. Verify:
   - no number gaps
   - no uncited final reference
   - no visible citation missing a reference
   - repeated source numbers are stable

Example:

```text
Body source order: A, B, A, C, B
Number map: A -> [1], B -> [2], C -> [3]
Final reference order: [1] A, [2] B, [3] C
```

## GB/T 7714-Style Formatting

Use these templates unless the user supplies a stricter journal format.

Journal paper:

```text
[n] Authors. Title[J]. Journal, Year, Volume(Issue): Pages. DOI.
```

Patent:

```text
[n] Inventors or Assignee. Patent title[P]. Jurisdiction: Patent number, Publication date.
```

Standard/code/guideline/regulation:

```text
[n] Standard number, Standard title[S]. Place: Publisher, Year.
```

Book:

```text
[n] Authors. Title[M]. Place: Publisher, Year.
```

Thesis:

```text
[n] Author. Title[D]. Institution, Year.
```

Report:

```text
[n] Authors or Organization. Title[R]. Place: Publisher/Organization, Year.
```

Web:

```text
[n] Authors or Organization. Title[EB/OL]. URL, access date.
```

If a field is unknown, omit the field or mark it in an audit note. Do not invent it.

## Deduplication

Deduplicate before final numbering by:

1. DOI exact match.
2. Patent number / standard number exact match.
3. Normalized title + year + first author/organization.
4. Manual user confirmation for ambiguous matches.

If two records conflict on DOI, patent number, or standard number, stop and flag the conflict.

## DOI And Identifier Handling

- Add DOI when available for paper/review sources.
- Do not fabricate DOI.
- Patent references should include patent/publication number when available.
- Standard/code references should include standard/code number and version year when available.
- If metadata is incomplete, write an audit note rather than silently filling values.

## Internal Evidence Logs

Internal data or notes should use a separate log:

```json
{
  "claim_id": "",
  "manuscript_section": "",
  "source_id": "",
  "source_class": "D_internal",
  "source_type": "dataset",
  "source_path": "",
  "evidence_location": "",
  "claim": "",
  "value": null,
  "unit": "",
  "cite_allowed": false,
  "reference_allowed": false
}
```

Internal evidence does not appear in final references unless the user explicitly changes permissions.

