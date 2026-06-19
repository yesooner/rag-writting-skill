---
name: query-planner
description: Create section-level query plans for RAG-based article writing. Use when Claude Code needs to turn a manuscript task, outline, section title, or research question into Introduction/Method/Results/Discussion retrieval queries before hybrid retrieval or section drafting.
---

# Query Planner

## Purpose

Use this skill before retrieval or section writing. It turns a paper outline into section-purpose queries so the agent does not search the card library with one vague global prompt.

## Required Inputs

Confirm or read:

```text
output_root
workflow_state.json
article title or topic
target section list
available source classes and card kinds
```

Do not write a query plan before `output_root` is known.

## Outputs

Write:

```text
<output_root>/queries/query_plan.json
```

Update:

```text
<output_root>/workflow_state.json
```

Set:

```json
{
  "query_plan_status": "ready"
}
```

## Script

Prefer the bundled script when a deterministic query plan is enough:

```powershell
python -X utf8 skills\query-planner\scripts\build_query_plan.py `
  --output-root "<output_root>" `
  --title "<article title>" `
  --sections "Introduction,Method,Results,Discussion"
```

## Query Plan Schema

Use this shape:

```json
{
  "article_id": "",
  "language": "zh",
  "queries": [
    {
      "query_id": "intro_background_001",
      "section": "Introduction",
      "section_purpose": "background",
      "query": "",
      "allowed_source_class": ["A_core", "B_background"],
      "preferred_content_kind": ["text", "citation", "result"],
      "preferred_source_type": ["paper", "review", "report"],
      "top_k": 12,
      "notes": ""
    }
  ]
}
```

AI-written `query`, `section_purpose`, and `notes` default to Chinese unless the user requests another language. Technical terms may stay in English.

## Default Section Queries

Use these defaults and adapt them to the topic:

```text
Introduction:
- background query
- research gap query
- state-of-the-art query

Method:
- model setup query
- parameter basis query
- standard/code query
- formula/metric query

Results:
- comparison query
- mechanism explanation query
- failure mode query

Discussion:
- limitation query
- contradiction query
- engineering implication query
```

## Source-Class Defaults

```text
Introduction -> A_core + B_background
Method -> C_method + A_core
Results -> A_core + C_method
Discussion -> A_core + B_background + C_method
```

## Content-Kind Defaults

```text
background -> text, citation
research_gap -> text, result, citation
state_of_the_art -> text, result, table
model_setup -> method, standard_clause, equation
parameter_basis -> method, table, data
standard_code -> standard_clause, method
formula_metric -> equation, method
comparison -> result, table, figure
mechanism_explanation -> result, figure, method
failure_mode -> result, figure
limitation -> text, result
contradiction -> result, table, citation
engineering_implication -> result, standard_clause, method
```

## Hard Rules

- Do not perform retrieval in this skill.
- Do not write manuscript prose in this skill.
- Do not mark retrieval as complete.
- Every query must include `section`, `section_purpose`, source-class filters, content-kind preferences, and `top_k`.
- If workflow state says carding is not ready, still create the query plan but mark `requires_cards=true`.
