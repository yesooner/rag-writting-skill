---
name: citation-registry
description: Register visible citations, order numbered references by first in-text citation, and generate Chinese-standard references for article writing. Use when Claude Code needs to create citation_registry.jsonl, fix in-text citation numbering, build a GB/T 7714-style reference list, deduplicate references, handle DOI/standard/patent metadata, or separate internal data evidence from final references.
---

# Citation Registry

## Core Rules

1. Final references follow Chinese citation practice, using GB/T 7714-style numbered references unless the user specifies another Chinese standard.
2. Reference numbering is determined only by the first visible in-text citation order.
3. Do not sort final references alphabetically, by year, by source class, by source type, or by ranking priority.
4. Repeated citations reuse the number assigned at first appearance.
5. In-text citation numbers and final reference-list numbers must be updated together.

## Scope

Use this skill after `article-rag-chunking` has produced source metadata/cards, or when repairing a draft manuscript's citations and final references.

Visible citation chain:

```text
visible manuscript claim -> citation_registry.jsonl -> first-appearance numbering -> GB/T 7714 reference list
```

Internal evidence chain:

```text
project data/internal note -> data_evidence_log.jsonl or internal_evidence_log.jsonl -> no final reference entry
```

## Citation Registry Workflow

When writing or repairing cited manuscript text:

1. Identify every visible in-text citation marker or cited claim.
2. Resolve each citation to a stable `source_id` or `cite_key`.
3. Reject sources with `cite_allowed=false` or `reference_allowed=false` from visible references.
4. Write one registry record per visible claim/source support in `citation_registry.jsonl`.
5. Scan the manuscript body from top to bottom.
6. Assign citation numbers by the first visible occurrence of each unique source.
7. Reuse the assigned number for repeated citations.
8. Rebuild the final reference list in that exact order.
9. Format the final list according to GB/T 7714-style rules.
10. Verify that every visible citation has a final reference and every final reference is cited.

Use `references/citation-registry-rules.md` for schemas and algorithms.

## Source Classes And Reference Permissions

Source class controls evidence role; it does not control numbering order.

| source_class | Default visible citation | Final reference | Notes |
|---|---:|---:|---|
| `A_core` | Yes, if allowed | Yes, if cited | Core evidence, target papers, key patents or standards |
| `B_background` | Yes, if allowed | Yes, if cited | Background and review sources |
| `C_method` | Yes, if allowed | Yes, if cited | Methods, standards, codes, protocols, metrics |
| `D_internal` | No by default | No by default | Project data, private reports, notes, unpublished material |

`cite_allowed` and `reference_allowed` override defaults. A/B/C sources still require both flags to enter visible citations and the final reference list.

## Source Types

Support at least:

```text
paper, review, patent, standard, code, guideline, regulation,
report, dataset, spreadsheet, note, book, thesis, web
```

Patent, standard, code, guideline, and regulation sources are not separate citation classes. They are source types. If visibly cited and allowed, they are numbered by first in-text citation position like any other source.

## Chinese Reference Standard

Default output is GB/T 7714-style numbered references:

```text
[1] Author. Title[J]. Journal, Year, Volume(Issue): Pages. DOI.
[2] Author. Title[P]. Country/Region: Patent number, Publication date.
[3] Standard number, Standard title[S]. Place: Publisher, Year.
[4] Author. Title[M]. Place: Publisher, Year.
[5] Author. Title[D]. Institution, Year.
[6] Author. Title[EB/OL]. URL, access date.
```

Use source metadata to choose the document type marker:

```text
paper/review -> [J]
patent -> [P]
standard/code/guideline/regulation -> [S] unless configured otherwise
book -> [M]
thesis -> [D]
web -> [EB/OL]
report -> [R]
dataset/spreadsheet/internal data -> not final reference unless explicitly allowed
```

Do not fabricate DOI, patent numbers, standard numbers, issue numbers, pages, URLs, or access dates.

## First-Citation Numbering

Required algorithm:

```text
read manuscript body
resolve each visible citation to source_id/cite_key
walk body from beginning to end
when a source appears first time, assign next integer
when it repeats, reuse existing integer
replace all in-text citation markers accordingly
rebuild final reference list in assigned-number order
verify continuous numbering
```

Do not only reorder the final reference list. The body and final list must be synchronized.

## Patents And Standards

For patents, preserve:

```text
patent_number
application_number
publication_number
jurisdiction
assignee
inventors
filing_date
publication_date
claims_used or cited section
```

For standards/codes/guidelines/regulations, preserve:

```text
standard_number
title
version_year
issuing_body
clause or section
clause_title
```

If a standard clause or patent claim supports a manuscript claim, record that location in the registry. Do not cite a standard or patent vaguely when a clause/claim can be identified.

## Final Checks

- Every visible citation has a `citation_registry.jsonl` record.
- Every final reference has at least one visible citation.
- Citation numbers are continuous from 1 to N.
- First source occurrence in the body determines its number.
- Repeated sources reuse the first number.
- A/B/C/D ranking does not alter citation numbering.
- D/internal data is not in the final reference list unless explicitly allowed.
- DOI/identifier fields are not fabricated.
- GB/T 7714-style type markers match source type.

