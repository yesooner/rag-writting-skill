# Card Schema

## Source Metadata

```json
{
  "source_id": "paper_001",
  "source_class": "A_core",
  "source_type": "paper",
  "title": "",
  "authors": [],
  "year": null,
  "journal": "",
  "doi": "",
  "standard_number": "",
  "patent_number": "",
  "source_path": "",
  "metadata_source": {
    "local_json": true,
    "crossref": false,
    "openalex": false,
    "user_supplied": false
  },
  "metadata_confidence": 0.0,
  "missing_metadata": []
}
```

## Card Record

```json
{
  "card_id": "",
  "source_id": "",
  "source_class": "",
  "source_type": "",
  "card_type": "",
  "content_kind": "",
  "title": "",
  "section_path": "",
  "source_location": {
    "page_start": null,
    "page_end": null,
    "line_start": null,
    "line_end": null,
    "clause": "",
    "claim_number": ""
  },
  "claim": "",
  "evidence_text": "",
  "keywords": [],
  "terms_en": [],
  "terms_zh": [],
  "preferred_translation": {},
  "rhetorical_role": "",
  "retrieval_triggers": [],
  "cite_allowed": true,
  "reference_allowed": true,
  "default_card_priority": 0.0,
  "confirmed_card_priority": null
}
```

## Content Kinds

Every card must carry one explicit `content_kind`.

```text
section
text
table
figure
equation
data
term
citation
standard_clause
patent_claim
method
result
```

Default mapping:

```text
section -> section_card
text -> section_card or evidence_card
table -> table_card
figure -> figure_card
equation -> equation_card
data -> data_card
term -> term_card
citation -> citation_card
standard_clause -> standard_card
patent_claim -> patent_card
method -> method_card
result -> result_card
```

## Structured JSON Block Input

When the cleaned source is JSON, each block should be normalized into the same card schema. Preferred block fields:

```json
{
  "type": "paragraph | table | figure | equation | data | section | claim | clause",
  "content_kind": "text",
  "text": "",
  "content": "",
  "markdown": "",
  "caption": "",
  "latex": "",
  "table": [],
  "rows": [],
  "section_path": [],
  "page": null,
  "line_start": null,
  "line_end": null
}
```

Accepted container keys:

```text
blocks
sections
pages
elements
chunks
cards
items
```

If both Markdown and structured JSON exist for the same source, prefer JSON for card generation.

## Source Classes

Definitions and permission defaults are owned by `source-role-policy`. RAG cards only store and consume the value.

```text
A_core
B_background
C_method
D_internal
unclassified
```

## Source Types

Allowed values and citation permission defaults are owned by `source-role-policy`.

```text
paper
review
patent
standard
code
guideline
regulation
report
dataset
spreadsheet
note
book
thesis
web
```

## Ranking Fields

```json
{
  "source_id": "",
  "source_class": "A_core",
  "source_type": "paper",
  "default_rank_in_class": 1,
  "confirmed_rank_in_class": null,
  "rank_confirmed_by_user": false,
  "rank_confirmed_at": null,
  "rank_reason": ""
}
```

## Retrieval Roles

```text
background
research_gap
literature_review
method
experiment_design
model_setup
material_property
standard_clause
patent_claim
result
comparison
mechanism
limitation
conclusion
terminology
citation_support
data_trace
```
