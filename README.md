# RAG Writing Skill


<p align="center">
  <a href="./README.md"><img alt="Language English" src="https://img.shields.io/badge/Language-English-lightgrey"></a>
  <a href="./README.zh-CN.md"><img alt="Language Chinese" src="https://img.shields.io/badge/%E8%AF%AD%E8%A8%80-%E4%B8%AD%E6%96%87-blue"></a>
  <a href="./LICENSE"><img alt="License MIT" src="https://img.shields.io/badge/License-MIT-orange"></a>
</p>

RAG Writing Skill is a Claude Code/Codex skill suite for preparing article sources, building typed RAG cards, planning section queries, running hybrid retrieval, checking claim-evidence links, repairing numbered citations, and applying user-confirmed Word formatting.

## Overview

This repository provides nine sub-skills:

```text
research-workflow
article-rag-chunking
source-role-policy
query-planner
hybrid-retrieval
section-writing-router
claim-evidence-checker
citation-registry
word-formatting
```

Default workflow:

```text
research-workflow
-> source-role-policy
-> article-rag-chunking
-> query-planner
-> hybrid-retrieval
-> section-writing-router
-> claim-evidence-checker
-> citation-registry
-> word-formatting, only when .docx formatting is requested
```

Use `research-workflow` when you need the full human-in-the-loop research process. Use `article-rag-chunking` directly when sources are already selected and only need RAG cards.

RAG-only workflow:

```text
source-role-policy
-> article-rag-chunking
-> query-planner
-> hybrid-retrieval
-> section-writing-router
-> claim-evidence-checker
-> citation-registry
-> word-formatting, only when .docx formatting is requested
```

## Claude Code Usage

After installing as a Claude Code plugin:

```text
/rag-writing-skill:research-workflow
/rag-writing-skill:article-rag-chunking
/rag-writing-skill:source-role-policy
/rag-writing-skill:query-planner
/rag-writing-skill:hybrid-retrieval
/rag-writing-skill:section-writing-router
/rag-writing-skill:claim-evidence-checker
/rag-writing-skill:citation-registry
/rag-writing-skill:word-formatting
```

Validate the plugin:

```powershell
claude plugin validate .
```

## Codex Usage

Codex does not rely on Claude Code slash commands. Trigger skills with natural language or explicit skill names:

```text
use research-workflow
use article-rag-chunking
use source-role-policy
use query-planner
use hybrid-retrieval
use section-writing-router
use claim-evidence-checker
use citation-registry
use word-formatting
```

## Environment

Use an isolated Python environment instead of conda `base`.

```powershell
python -m pip install -r requirements.txt
```

or:

```powershell
conda env create -f environment.yml
conda activate rag-writing-skill
```

Verify the release candidate:

```powershell
python -X utf8 scripts\verify_release.py --root .
```

## research-workflow

Purpose: run the full human-in-the-loop research process from topic definition to final report preparation.

Default process:

```text
human topic definition
-> AI-assisted search
-> human screening
-> AI evidence organization
-> human conclusion confirmation
-> AI review/report draft
-> human revision and finalization
```

Compact default outputs:

```text
<output_root>\research_brief.md
<output_root>\workflow_state.json
<output_root>\source_candidates.csv
<output_root>\evidence_registry.csv
<output_root>\human_decisions.md
<output_root>\report_draft_v1.md
<output_root>\qa_checklist.md
```

Report drafts and final reports use versioned names such as `report_draft_v1.md`, `report_draft_v2.md`, and `final_report_v1.md`; existing versioned report files must not be overwritten. User-visible outputs default to Chinese unless the user requests another language, while original titles, identifiers, proper nouns, and exact quotations may stay in their source language.

Supported research tracks include papers, reviews, patents, standards, codes, guidelines, regulations, technical specifications, reports, datasets, and web sources. Optional tracks may be marked `not_searched` or `needed_later`; missing sources must not be fabricated.

For RAG-based manuscript writing, workflow state prevents skipped steps:

```text
workflow_state.json
query_plan_status -> retrieval_status -> section_draft_status -> claim_check_status -> citation_status
```

## article-rag-chunking

Purpose: ingest source files, extract local and optional external metadata, generate typed RAG cards, and produce a default source ranking table for user confirmation.

Key constraints:

- Ask for `output_root` before writing any generated RAG file.
- Keep all outputs under `<output_root>`.
- Support Markdown/Text and structured JSON as carding inputs.
- Prefer structured JSON over Markdown when both exist for the same `source_id`, unless JSON contains only metadata.
- Do not fabricate DOI, citation counts, journal metrics, or missing identifiers.
- Do not write confirmed ranking before user confirmation.

Main output folders:

```text
<output_root>\cleaned
<output_root>\metadata
<output_root>\cards
<output_root>\ranking
<output_root>\logs
```

Main output files:

```text
<output_root>\metadata\metadata_raw.jsonl
<output_root>\metadata\metadata_enriched.jsonl
<output_root>\cards\*.jsonl
<output_root>\ranking\default_source_ranking.md
<output_root>\ranking\default_source_ranking.json
<output_root>\logs\pipeline_steps.json
```

Supported `content_kind` values:

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

Common mappings:

```text
body paragraph -> text -> section_card or evidence_card
section heading -> section -> section_card
table -> table -> table_card
figure/image/caption -> figure -> figure_card
equation/equation note -> equation -> equation_card
Excel/CSV/data description -> data -> data_card
term definition/bilingual term -> term -> term_card
reference entry/citation context -> citation -> citation_card
standard clause -> standard_clause -> standard_card
patent claim/abstract/description fragment -> patent_claim -> patent_card
method step/algorithm/model setup -> method -> method_card
result/mechanism/comparison/conclusion evidence -> result -> result_card
```

Standard pipeline:

```powershell
python -X utf8 skills\article-rag-chunking\scripts\run_rag_pipeline.py `
  --input-dir "<source-folder>" `
  --output-root "<output_root>" `
  --providers crossref,openalex
```

Local-only mode:

```powershell
python -X utf8 skills\article-rag-chunking\scripts\run_rag_pipeline.py `
  --input-dir "<source-folder>" `
  --output-root "<output_root>" `
  --no-network
```

## query-planner

Purpose: split a manuscript task into section-level retrieval queries.

Output:

```text
<output_root>\queries\query_plan.json
```

Script:

```powershell
python -X utf8 skills\query-planner\scripts\build_query_plan.py `
  --output-root "<output_root>" --title "<article title>"
```

Default section purposes:

```text
Introduction: background, research gap, state of the art
Method: model setup, parameter basis, standard/code, formula/metric
Results: comparison, mechanism explanation, failure mode
Discussion: limitation, contradiction, engineering implication
```

## hybrid-retrieval

Purpose: retrieve evidence from cards with BM25 or keyword retrieval, optional dense retrieval, source-class filters, content-kind filters, and section-purpose reranking.

Output:

```text
<output_root>\retrieval\retrieval_trace.jsonl
```

Script:

```powershell
python -X utf8 skills\hybrid-retrieval\scripts\retrieve_cards.py `
  --output-root "<output_root>"
```

## section-writing-router

Purpose: route each manuscript section through section-specific RAG strategy.

```text
Introduction -> A_core + B_background
Method -> C_method + standard/equation/method cards
Results -> A_core + result/table/figure cards
Discussion -> A_core + contradiction + limitation evidence
```

## claim-evidence-checker

Purpose: check every factual claim against evidence cards, source permissions, locations, and citation records.

Outputs:

```text
<output_root>\claims\claim_registry.jsonl
<output_root>\claims\evidence_units.jsonl
<output_root>\claims\claim_evidence_map.jsonl
<output_root>\qa\unsupported_claims.csv
<output_root>\qa\weak_evidence_claims.csv
<output_root>\qa\citation_mismatch.csv
```

Script:

```powershell
python -X utf8 skills\claim-evidence-checker\scripts\check_claim_evidence.py `
  --output-root "<output_root>"
```

Required checks:

```text
fact claims need source_id
key claims need page_or_location
formula claims need equation_card or C_method source
result claims need result/table/figure evidence
D_internal is not public reference evidence by default
```

## source-role-policy

Purpose: classify sources and set citation/reference permissions.

Source classes:

```text
A_core
B_background
C_method
D_internal
unclassified
```

| source_class | Meaning | Visible citation default | Final reference default |
|---|---|---:|---:|
| `A_core` | Core target source, main evidence, key comparison, core patent, or core standard | Yes | Yes |
| `B_background` | Background, review, research status, and problem framing | Yes | Yes |
| `C_method` | Method, model, protocol, standard, formula, metric, or terminology | Yes | Yes |
| `D_internal` | Project data, internal report, note, private file, or unpublished material | No | No |
| `unclassified` | Temporary state that requires user confirmation | No | No |

Source types:

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
spreadsheet
note
book
thesis
web
```

Important rules:

- `source-role-policy` owns the A/B/C/D definitions.
- Patents, standards, codes, guidelines, regulations, and technical specifications are source types.
- `D_internal` defaults to internal evidence only.
- `source_class` never determines bibliography numbering.

## citation-registry

Purpose: register visible citations, assign reference numbers by first in-text appearance, deduplicate sources, and rebuild GB/T 7714-style numbered references.

Rules:

- Number references by first visible in-text citation.
- Reuse the first number for repeated citations.
- Synchronize body citation numbers and final reference list numbers.
- Do not sort references by source class, ranking, author, year, or perceived importance.
- Do not fabricate DOI or identifiers.
- Keep internal data evidence out of the final reference list unless explicitly allowed.

Suggested visible citation chain:

```text
visible manuscript claim
-> citation_registry.jsonl
-> first-appearance numbering
-> GB/T 7714-style reference list
```

Internal evidence chain:

```text
project data/internal note
-> data_evidence_log.jsonl or internal_evidence_log.jsonl
-> no final reference entry
```

Common document type markers:

```text
paper/review -> [J]
patent -> [P]
standard/code/guideline/regulation/technical_specification -> [S]
book -> [M]
thesis -> [D]
web -> [EB/OL]
report -> [R]
```

Final checks:

- Every visible citation has a registry record.
- Every final reference is cited at least once.
- Numbering is continuous from 1 to N.
- Repeated citations reuse the first number.
- Internal data does not enter the final reference list by default.

## word-formatting

Purpose: inspect and apply `.docx` formatting from a user-confirmed style table.

The required confirmation table includes:

| Part | Style name | Chinese font | English font | Size pt | Bold | Alignment | Line spacing | Space before pt | Space after pt | First-line indent | Notes |
|---|---|---|---|---:|---|---|---:|---:|---:|---|---|
| Body | Body | SimSun | Times New Roman | 12 | No | Justify | 1.5 | 0 | 0 | 2 chars | Main paragraphs |
| Heading 1 | H1 | SimHei | Times New Roman | 14 | Yes | Left | 1.5 | 0 | 0 | None | Top-level sections |
| Heading 2 | H2 | SimHei | Times New Roman | 12 | Yes | Left | 1.5 | 0 | 0 | None | Second-level sections |
| Figure caption | Figure Caption | SimSun | Times New Roman | 10.5 | Yes | Center | 1.0 | 0 | 0 | None | Caption below figure |
| Table caption | Table Caption | SimSun | Times New Roman | 10.5 | Yes | Center | 1.0 | 0 | 0 | None | Caption above table |
| Table text | Table Text | SimSun | Times New Roman | 10.5 | No | Center | 1.0 | 0 | 0 | None | Table body |
| Reference | Reference | SimSun | Times New Roman | 10.5 | No | Justify | 1.0 | 0 | 0 | Hanging | Final references |
| Formula | Formula | Cambria Math | Cambria Math | 12 | No | Center | 1.0 | 0 | 0 | None | Display equations |

Supported configuration areas:

- page setup
- header/footer
- style names and typography
- paragraph classification patterns
- figure wrapping
- table formatting
- citation superscripting
- formula protection
- CJK-alphanumeric spacing normalization

Figure and caption rules:

- Figures and captions may be placed in a one-column, two-row table.
- The first row contains the figure.
- The second row contains the caption.
- Caption font size is controlled by the confirmed style table.

Citation superscript rules:

- In-text markers such as `[3]` may be superscripted by configuration.
- Reference-list labels such as `[3]` are not superscripted by default unless explicitly configured.

CJK-alphanumeric spacing rules:

- Do not keep spaces between CJK characters and Latin letters or Arabic digits.
- `CJK_char love CJK_char` should become `CJK_charloveCJK_char`.
- `CJK_char 1 CJK_char model` should become `CJK_char1CJK_charmodel`.
- The inspection report includes `cjk_alnum_spacing_issue_count`, `cjk_latin_spacing_issue_count`, and examples.
- The formatter removes these spaces only when the confirmed config enables `normalize_cjk_latin_spacing`.

Formula protection rules:

- Check formula nodes or formula XML hashes before and after formatting.
- Abort rather than save if formula or image counts are abnormal.
- Do not change manuscript text content.

Common commands:

```powershell
python -X utf8 skills\word-formatting\scripts\format_docx.py `
  --write-template "<config.json>"

python -X utf8 skills\word-formatting\scripts\inspect_docx.py `
  --docx "<target.docx>" --config "<confirmed-config.json>"

python -X utf8 skills\word-formatting\scripts\format_docx.py `
  --docx "<target.docx>" --config "<confirmed-config.json>"
```

The final report should include:

- target file path
- backup file path
- style completeness
- image count
- figure-table count
- top-level loose image paragraph count
- in-text citation count and superscript count
- reference-list number superscript count
- formula node count and hash status
- regular table count
- CJK-Alphanumeric Spacing issue count and examples
- CJK-alphanumeric spaces removed, when normalization is enabled

## Directory Layout

```text
.claude-plugin/
skills/
  research-workflow/
  article-rag-chunking/
  source-role-policy/
  query-planner/
  hybrid-retrieval/
  section-writing-router/
  claim-evidence-checker/
  citation-registry/
  word-formatting/
scripts/
requirements.txt
environment.yml
request.txt
README.md
README.zh-CN.md
```

