---
name: source-role-policy
description: Define and assign generic source classes, source types, citation permissions, and internal-evidence boundaries for article writing workflows. Use when Claude Code needs to classify paper, patent, standard, code, report, dataset, note, or web sources into A/B/C/D roles before RAG carding, citation registry, ranking, or manuscript evidence planning.
---

# Source Role Policy

## Scope

Use this skill to classify sources and decide citation permissions. This skill owns ABCD definitions.

`article-rag-chunking` must consume `source_class` and `source_type`; it must not redefine them.

## Source Classes

Use these classes:

```text
A_core
B_background
C_method
D_internal
unclassified
```

Definitions:

- `A_core`: core target sources, main evidence, key comparison sources, core patents, core standards, or sources central to the article's argument.
- `B_background`: background, review, research status, problem framing, and broad contextual sources.
- `C_method`: methods, models, protocols, experimental procedures, formulas, metrics, terminology, standards, codes, and guidelines.
- `D_internal`: project data, internal reports, user notes, unpublished material, private files, spreadsheets, and internal-only inspiration.
- `unclassified`: temporary state when the agent cannot confidently assign A/B/C/D. Must be shown to the user for confirmation before final ranking.

## Source Types

Use `source_type` to identify source form:

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

Patent, standards, codes, guidelines, regulations, and technical specifications are source types, not separate classes.

## Permission Defaults

| source_class | cite_allowed default | reference_allowed default | evidence log |
|---|---:|---:|---|
| `A_core` | true | true | optional |
| `B_background` | true | true | optional |
| `C_method` | true | true | optional |
| `D_internal` | false | false | required if used |
| `unclassified` | false | false | optional until confirmed |

The user or source metadata may override defaults, but overrides must be explicit.

## Classification Workflow

1. Read local source metadata from JSON/card records.
2. Determine `source_type`.
3. Assign a tentative `source_class`.
4. Set `cite_allowed` and `reference_allowed` from defaults.
5. If classification is uncertain, set `source_class=unclassified`.
6. Present unclassified or ambiguous sources to the user.
7. Write confirmed classification back to metadata/cards.

Use `references/source-role-rules.md` for details and examples.

## Patent And Standard Rules

Patent sources:

- Use `source_type=patent`.
- Put in `A_core` if central to the article argument or innovation route.
- Put in `C_method` if used for construction method, mechanism, claim alignment, or technical implementation.
- Put in `D_internal` if used only as internal inspiration and not visibly cited.

Standard/code/guideline/regulation/technical specification sources:

- Use the matching `source_type`.
- Put in `C_method` when used for methods, design constraints, test protocols, formulas, or evaluation criteria.
- Put in `A_core` only if the article is centrally built around that standard/code.
- Record clause or section when possible.

## Hard Rules

- Do not let `article-rag-chunking` redefine ABCD classes.
- Do not allow `unclassified` sources to become final confirmed rankings.
- Do not allow `D_internal` sources into final references unless the user explicitly changes permissions.
- `source_class` never determines citation number order; `citation-registry` orders references only by first visible in-text citation.
- If source role conflicts with user metadata, keep both values in an audit note and ask for confirmation.

## Related Skills

Use `article-rag-chunking` after assigning or confirming source roles.
Use `citation-registry` for visible citations and GB/T 7714-style references.

