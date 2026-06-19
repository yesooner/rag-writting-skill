---
name: article-rag-chunking
description: Clean article JSON/Markdown sources, extract and optionally enrich external metadata, create typed RAG cards, and generate user-confirmed ABCD-grouped ranking tables for article writing. Use when Claude Code needs to process paper, patent, standard, report, data, or note sources into retrieval-ready cards without project-specific assumptions.
---

# Article RAG Chunking

## Scope

Use this skill for source ingestion and retrieval preparation, not manuscript writing.

## Highest Priority: First-Call Output Root Gate

On the first call for a RAG job, ask the user for `output_root` before writing any generated file.

Do not run extraction, cleaning, enrichment, carding, ranking, or logging until `output_root` is confirmed.

Prompt the user with:

```text
Please provide the RAG output root directory, for example:`n<workspace>\rag_output\<article_or_project_name>`n`nAfter confirmation, the pipeline will create:`n<output_root>\cleaned
<output_root>\metadata
<output_root>\cards
<output_root>\ranking
<output_root>\logs
```

After confirmation, all generated outputs must stay under `output_root`, except an external metadata cache path explicitly provided by the user.

## Pipeline

```text
JSON + Markdown sources
-> metadata extraction
-> source role assignment by source-role-policy
-> optional metadata enrichment
-> cleaning and denoising
-> typed card generation
-> ABCD grouped default ranking table
-> user confirmation
-> confirmed ranking and retrieval-ready card files
```

## Inputs

Accept paired or standalone source files:

```text
paper.json + paper.md
patent.json + patent.md
standard.json + standard.md
technical_specification.json + technical_specification.md
report.json + report.md
dataset.json + data_summary.md
note.json + note.md
```

The cleaned/card source may be Markdown/Text or structured JSON. Do not assume Markdown is the only carding input.

Accepted carding inputs:

```text
cleaned Markdown/Text: *.md, *.txt
structured cleaned JSON: *.json
layout JSON from OCR/parser tools
block JSON from paper cleaning agents
source metadata JSON plus abstract/text/content fields
```

For structured JSON, prefer explicit block arrays such as:

```text
blocks
sections
pages
elements
chunks
cards
items
```

Each JSON block should preserve, when available:

```text
content_kind or type
text/content/markdown/latex/caption/table/rows
section_path or heading/title
page/page_number
line_start/line_end
```

Prefer local JSON metadata first. External metadata lookup is optional and must never fabricate missing values.

## Recommended Controller Script

After the user confirms `output_root`, prefer the controller script for the standard pipeline:

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'

& <python> -X utf8 `
  ${CLAUDE_PLUGIN_ROOT}\skills\article-rag-chunking\scripts\run_rag_pipeline.py `
  --input-dir "<source-folder>" `
  --output-root "<output_root>" `
  --providers crossref,openalex
```

For local-only metadata enrichment:

```powershell
& <python> -X utf8 `
  ${CLAUDE_PLUGIN_ROOT}\skills\article-rag-chunking\scripts\run_rag_pipeline.py `
  --input-dir "<source-folder>" `
  --output-root "<output_root>" `
  --no-network
```

The controller script writes only under `output_root` and generates:

```text
<output_root>\metadata\metadata_raw.jsonl
<output_root>\metadata\metadata_enriched.jsonl
<output_root>\cards\*.jsonl
<output_root>\ranking\default_source_ranking.md
<output_root>\ranking\default_source_ranking.json
<output_root>\logs\pipeline_steps.json
<output_root>\rag_pipeline_manifest.json
```

The controller script must not write `confirmed_source_ranking.json`; user confirmation is still required.

## Manual Script Steps

Use these only when the controller script is not appropriate.

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'

& <python> -X utf8 `
  ${CLAUDE_PLUGIN_ROOT}\skills\article-rag-chunking\scripts\extract_metadata.py `
  --input-dir "<source-folder>" --output "<output_root>\metadata\metadata_raw.jsonl"

& <python> -X utf8 `
  ${CLAUDE_PLUGIN_ROOT}\skills\article-rag-chunking\scripts\enrich_metadata.py `
  --input "<output_root>\metadata\metadata_raw.jsonl" `
  --output "<output_root>\metadata\metadata_enriched.jsonl" `
  --providers crossref,openalex --cache "<output_root>\metadata\cache"

& <python> -X utf8 `
  ${CLAUDE_PLUGIN_ROOT}\skills\article-rag-chunking\scripts\generate_cards.py `
  --input-dir "<source-folder>" `
  --metadata "<output_root>\metadata\metadata_enriched.jsonl" `
  --output-dir "<output_root>\cards"

& <python> -X utf8 `
  ${CLAUDE_PLUGIN_ROOT}\skills\article-rag-chunking\scripts\rank_sources.py `
  --input "<output_root>\metadata\metadata_enriched.jsonl" `
  --ranking-md "<output_root>\ranking\default_source_ranking.md" `
  --ranking-json "<output_root>\ranking\default_source_ranking.json"
```

Use `--no-network` for local-only enrichment.

## Metadata Workflow

1. Extract local metadata from JSON/MD.
2. Use `source-role-policy` to assign or confirm `source_class`, `source_type`, `cite_allowed`, and `reference_allowed`.
3. If classification is uncertain, keep `source_class=unclassified`.
4. Optionally enrich missing metadata using Crossref/OpenAlex or local metric tables.
5. Keep user/local fields as authoritative unless an exact DOI match proves a correction.
6. Record provider, match method, confidence, and missing fields.
7. Use enriched metadata only for default ranking suggestions.
8. Ask the user to confirm ranking before writing confirmed ranks.

## Chunk And Card Types

Chunk type must be explicit. Do not store every source fragment as one generic text chunk.

Card generation must support both:

```text
Markdown/Text chunks
Structured JSON blocks
```

If a cleaning agent outputs JSON, use the JSON block structure directly instead of converting it back to Markdown unless conversion is necessary to recover missing content. If both JSON and Markdown exist for the same `source_id`, prefer the structured JSON as the carding source because it usually preserves page, block, figure, table, and formula metadata better.

Each card must include `content_kind`:

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

Use these mappings by default:

```text
Article body paragraph -> content_kind=text -> section_card or evidence_card
Section heading -> content_kind=section -> section_card
Table -> content_kind=table -> table_card
Figure/image/caption -> content_kind=figure -> figure_card
Equation/equation note -> content_kind=equation -> equation_card
Excel/CSV/data description -> content_kind=data -> data_card
Term definition/bilingual term -> content_kind=term -> term_card
Reference entry/citation context-> content_kind=citation -> citation_card
Standard clause -> content_kind=standard_clause -> standard_card
Patent claim/abstract/description fragment-> content_kind=patent_claim -> patent_card
Method step/algorithm/model setup -> content_kind=method -> method_card
Result/mechanism/comparison/conclusion evidence-> content_kind=result -> result_card
```

Typed chunking is required because retrieval triggers differ:

```text
figure_card: figure number, caption, visual object, discussed result
equation_card: equation symbol, metric name, derivation purpose
data_card: source folder, workbook, sheet, series, column pair, metric
table_card: table title, row/column meaning, reported indicators
standard_card: standard number, clause, parameter or rule
patent_card: patent number, claim/abstract/description location
```

For complex PDF/OCR layout, use a layout parser such as MinerU first, then convert recovered JSON blocks into the same `content_kind` schema.

## Ranking Workflow

Default ranking must be grouped by source class:

```text
A_core -> B_background -> C_method -> D_internal -> unclassified
```

Do not mix source classes into one global ranking table.

Before generating the ranking table, ensure `output_root` has already been confirmed. The ranking table must be written to `<output_root>\ranking\default_source_ranking.md`, not only printed in chat. If the user explicitly provides a different ranking-table path, it must still be inside `output_root` unless the user explicitly approves an exception.

The generated Markdown table is a suggestion only. The user must confirm or adjust group-internal ordering before any `confirmed_rank_in_class` or retrieval priority is written.

## Source Classes

`article-rag-chunking` does not own source-class definitions. Classification rules are owned by `source-role-policy`.

Every source/card must carry one of these values:

```text
A_core
B_background
C_method
D_internal
unclassified
```

RAG uses `source_class` only for:

```text
card fields
grouped ranking tables
retrieval routing
citation/data separation hints
```

If a source remains `unclassified`, keep it in the `unclassified` ranking group and ask the user to confirm classification before final ranking.

Use `source_type` for source form; allowed values and permission defaults are defined in `source-role-policy`.

## Citation Permissions

- A/B/C sources may be citeable if `cite_allowed=true` and `reference_allowed=true`.
- D sources default to `cite_allowed=false` and `reference_allowed=false`.
- D sources support internal evidence logs, not final reference lists.
- A/B/C patent, standard, code, guideline, and regulation sources enter references only when visibly cited.
- Standards and codes must record clause or section when used.
- Technical specifications must record section, clause, table, figure, or requirement identifier when used.
- Patents must record claim, abstract, or description location when used.

## Card Generation

Generate generic cards, not project-specific chunks:

```text
source_card
section_card
evidence_card
method_card
result_card
table_card
figure_card
equation_card
term_card
citation_card
data_card
standard_card
patent_card
```

Every card must include `content_kind` and `retrieval_triggers`. Use `references/card-schema.md`.

## Output Layout

Required output under confirmed `output_root`:

```text
<output_root>\cleaned
<output_root>\metadata
<output_root>\cards
<output_root>\ranking
<output_root>\logs
```

Files:

```text
<output_root>\metadata\metadata_raw.jsonl
<output_root>\metadata\metadata_enriched.jsonl
<output_root>\ranking\default_source_ranking.md
<output_root>\ranking\default_source_ranking.json
<output_root>\ranking\confirmed_source_ranking.json
<output_root>\cards\*.jsonl
<output_root>\logs\*.jsonl
```

## Hard Rules

1. First call for a RAG job must ask the user to confirm `output_root`.
2. No generated RAG file may be written before `output_root` is confirmed.
3. All generated outputs must stay under `output_root`, except a cache path explicitly approved by the user.
4. RAG chunking does not write the final article.
5. Local JSON metadata is read first.
6. External metadata enrichment is optional and may be disabled.
7. Missing external metadata remains `null` or `unknown`; never invent it.
8. Default ranking must be grouped by A/B/C/D plus `unclassified`.
9. Default ranking is not confirmed ranking.
10. No `confirmed_rank_in_class` is written before user confirmation.
11. Source-class definitions and citation permission defaults come from `source-role-policy`.
12. `unclassified` sources must be shown to the user and cannot become confirmed final rankings until classified.
13. D-class material is not ordinary citeable literature.
14. Cards must contain `content_kind` and `retrieval_triggers`.


