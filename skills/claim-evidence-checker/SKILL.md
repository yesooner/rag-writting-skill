---
name: claim-evidence-checker
description: Check manuscript claims against RAG evidence, source permissions, locations, and citation records. Use when Claude Code needs to build claim registries, map claims to evidence cards, find unsupported or weak claims, and produce QA files before citation finalization or manuscript delivery.
---

# Claim Evidence Checker

## Purpose

Use this skill after section drafting and before `citation-registry`. It enforces the claim-evidence-citation loop.

## Required Inputs

Read available files under `output_root`:

```text
workflow_state.json
retrieval/retrieval_trace.jsonl
cards/*.jsonl
section drafts or manuscript draft
citation_registry.jsonl if already present
```

## Core Claim Files

Create or update:

```text
<output_root>/claims/claim_registry.jsonl
<output_root>/claims/evidence_units.jsonl
<output_root>/claims/claim_evidence_map.jsonl
```

QA outputs:

```text
<output_root>/qa/unsupported_claims.csv
<output_root>/qa/weak_evidence_claims.csv
<output_root>/qa/citation_mismatch.csv
```

Update:

```text
<output_root>/workflow_state.json
```

Set:

```json
{
  "claim_check_status": "ready"
}
```

## Script

Use the bundled checker for explicit `source_id`/`card_id` evidence tags in section drafts:

```powershell
python -X utf8 skills\claim-evidence-checker\scripts\check_claim_evidence.py `
  --output-root "<output_root>"
```

## Claim Registry

Each factual claim gets one record:

```json
{
  "claim_id": "",
  "section": "",
  "claim_text": "",
  "claim_type": "fact|formula|method|result|comparison|mechanism|limitation|interpretation",
  "importance": "key|normal|minor",
  "needs_citation": true,
  "status": "supported|weak|unsupported|internal_only|citation_mismatch"
}
```

## Evidence Unit

Each usable evidence unit gets one record:

```json
{
  "evidence_id": "",
  "card_id": "",
  "source_id": "",
  "source_class": "",
  "source_type": "",
  "content_kind": "",
  "evidence_text": "",
  "page_or_location": "",
  "cite_allowed": true,
  "reference_allowed": true
}
```

## Claim-Evidence Map

```json
{
  "claim_id": "",
  "evidence_id": "",
  "support_level": "strong|partial|weak|contradicts",
  "citation_required": true,
  "citation_key_or_number": "",
  "notes": ""
}
```

## Check Rules

```text
1. Every factual claim must have source_id.
2. Every key claim must have page_or_location.
3. Every formula claim must have equation_card or C_method source.
4. Every result claim must have result_card, table_card, or figure_card.
5. D_internal defaults to internal evidence and must not enter public references.
6. Unsupported claims must enter qa/unsupported_claims.csv.
7. Weak or partial evidence must enter qa/weak_evidence_claims.csv.
8. Citation/evidence disagreement must enter qa/citation_mismatch.csv.
```

## CSV Columns

`unsupported_claims.csv`:

```text
claim_id,section,claim_text,claim_type,reason,suggested_action
```

`weak_evidence_claims.csv`:

```text
claim_id,section,claim_text,evidence_id,support_level,weakness,suggested_action
```

`citation_mismatch.csv`:

```text
claim_id,section,claim_text,citation_key_or_number,source_id,issue,suggested_action
```

## Hard Rules

- Do not silently delete unsupported claims.
- Do not upgrade weak evidence to strong evidence for prose convenience.
- Do not allow D_internal evidence into public references unless the user explicitly overrides permission.
- Do not finalize references until unsupported and mismatch files have been reviewed.
