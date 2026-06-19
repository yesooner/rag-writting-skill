---
name: research-workflow
description: Run a compact human-in-the-loop research workflow for literature, patent, standard, code, guideline, report, dataset, and web-source investigation. Use when Claude Code needs to support topic definition, AI-assisted search, human screening, evidence extraction, human conclusion confirmation, draft review writing, and final report preparation without project-specific paths.
---

# Research Workflow

## Purpose

Use this skill to run this workflow:

```text
human topic definition
-> AI-assisted search
-> human screening
-> AI evidence organization
-> human conclusion confirmation
-> AI review/report draft
-> human revision and finalization
```

This skill coordinates research work. It does not replace `article-rag-chunking`, `source-role-policy`, or `citation-registry`; call those skills when source carding, source-role classification, or formal citation numbering is needed.

## First Step

Before writing files, ask the user to confirm:

```text
research question/topic
search boundary
source types to include
output_root
language requirements
```

Keep all generated files under `output_root`.

Default language is Chinese for all user-visible outputs. Keep original English titles, patent titles, standard numbers, DOI, organization names, proper nouns, and exact source quotations when needed. CSV column names may stay in English, but AI-written summaries, notes, decisions, and report prose should be Chinese unless the user explicitly requests another language.

## Source Tracks

Support these source tracks:

```text
paper
review
patent
standard
code
guideline
regulation
technical_specification
report
dataset
web
```

Patent, standard, code, guideline, regulation, and technical specification tracks are optional. If they are not available in the current project, leave their status as `not_searched` or `needed_later`; do not fabricate sources.

For source roles and citation permissions, use `source-role-policy`.

## Compact Output Set

Do not create many fragmented files by default. Write only these core files unless the user asks for more:

```text
<output_root>/research_brief.md
<output_root>/source_candidates.csv
<output_root>/evidence_registry.csv
<output_root>/human_decisions.md
<output_root>/report_draft_v1.md
<output_root>/qa_checklist.md
```

Optional files:

```text
<output_root>/search_log.jsonl
<output_root>/missing_items.csv
<output_root>/final_report_v1.md
```

Use optional files only when they reduce ambiguity or preserve important audit information.

Versioned report filenames are required:

```text
report_draft_v1.md
report_draft_v2.md
final_report_v1.md
final_report_v2.md
```

Never overwrite an existing report draft or final report. Use the next available version number. Registries and checklists may be updated in place because they represent the current research state.

## Workflow

### 1. Define The Task

Create or update `research_brief.md` with:

```text
topic
research questions
application context
time range
included source types
excluded source types
keywords/search terms
expected report form
```

Ask the user to confirm the brief before broad search.

Human gate: stop after writing or showing `research_brief.md` until the user confirms the topic, boundary, included source types, excluded source types, output root, and language.

### 2. Search And Collect Candidates

Search or ingest user-provided sources. Normalize candidates into `source_candidates.csv`.

Required columns:

```text
source_id
source_type
title
authors_or_assignee
year
identifier
venue_or_authority
source_url_or_path
search_query
relevance_score
status
notes
```

Use `identifier` for DOI, patent number, standard number, report number, URL, or local stable id. Leave unknown values empty; do not invent them.

Allowed `status` values:

```text
candidate
selected
rejected
need_more_search
not_searched
needed_later
```

### 3. Human Screening Gate

Show the candidate table or a concise grouped summary to the user.

Do not extract final evidence or write report conclusions until the user marks sources as `selected`, `rejected`, or `need_more_search`.

Human gate: if the user has not screened candidates, update only `source_candidates.csv` and ask for screening confirmation.

### 4. Extract Evidence

For selected sources, write `evidence_registry.csv`.

Required columns:

```text
evidence_id
source_id
source_type
evidence_type
claim_or_fact
method_or_context
page_or_location
confidence
used_in_report
notes
```

Allowed `evidence_type` values:

```text
paper_fact
patent_fact
standard_clause
code_clause
guideline_rule
regulation_rule
technical_spec
data_fact
method_fact
ai_summary
human_judgement
```

Every report claim must trace to `evidence_registry.csv` or `human_decisions.md`.

Human gate: evidence may be extracted by AI, but conclusions and countermeasures remain proposals until the user records a decision in `human_decisions.md`.

### 5. Identify Missing Items

If evidence is weak or missing, write a short section in `research_brief.md` or create `missing_items.csv`.

Track missing:

```text
key paper
key patent
standard/code/guideline basis
technical specification
application context
method evidence
data support
countermeasure basis
```

### 6. Human Conclusion Gate

Write proposed conclusions and countermeasures into `human_decisions.md`.

Each item must have one of:

```text
accepted
revise
discussion_only
delete
need_more_evidence
```

Do not move a conclusion into `report_draft_vN.md` unless it is `accepted` or explicitly allowed by the user.

### 7. Draft The Report

Write the next available `report_draft_vN.md` only from:

```text
research_brief.md
evidence_registry.csv
human_decisions.md
selected source metadata
```

Use a concise structure unless the user asks for a long report:

```text
title
abstract or executive summary
background and problem
source screening summary
evidence synthesis
countermeasures or research recommendations
limitations and missing evidence
references or source list
```

If formal references are required, call `citation-registry`.

Human gate: after generating a draft, ask the user to revise, accept, or request another version. If the user asks for a final version, write the next available `final_report_vN.md` rather than overwriting an earlier file.

### 8. QA

Write `qa_checklist.md` with:

```text
all report claims have evidence ids
all selected sources appear in evidence registry or have a reason for no use
all conclusions have human decision status
patents have publication/application numbers when available
standards/codes/guidelines include clause or section when available
no fabricated DOI, patent number, standard number, citation count, or authority
internal/project data is separated from visible references
```

## Hard Rules

- Do not use project-specific paths.
- Do not force a fixed search tool; use available local/web/MCP tools appropriate to the environment.
- Do not treat AI summaries as final evidence without source linkage.
- Do not write unsupported conclusions.
- Do not overproduce documents; use the compact output set by default.
- Do not cite internal files as public references unless the user explicitly permits it.
- Do not overwrite versioned report files.
- Write user-facing outputs in Chinese by default, except original titles, identifiers, proper nouns, and exact quotations.
