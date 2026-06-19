# Source Role Rules

## Core Decision

Classify every source using two independent fields:

```json
{
  "source_class": "A_core",
  "source_type": "paper"
}
```

`source_class` answers: what role does this source play in the article?

`source_type` answers: what kind of source is it?

## Source Class Examples

### A_core

Use when the source is central to the paper's argument.

Examples:

- main target paper
- key comparison paper
- central dataset description paper
- patent central to article novelty
- standard/code central to the article objective
- technical specification central to the article objective

### B_background

Use for background and literature review.

Examples:

- review article
- broad field background paper
- research status source
- problem-framing report

### C_method

Use for methods and technical support.

Examples:

- method paper
- experimental protocol
- model/calculation source
- evaluation metric definition
- standard clause
- code provision
- technical specification requirement
- terminology source

### D_internal

Use for non-public or non-reference-list evidence.

Examples:

- local spreadsheet
- internal report
- user note
- draft manuscript
- private data folder
- local image set
- internal-only patent/standard note

### unclassified

Use when the source cannot be confidently classified. Do not silently guess when the role affects citation visibility, ranking, or evidence use.

## Source Type Examples

```text
paper: ordinary journal or conference paper
review: review or survey article
patent: patent, patent application, utility model
standard: formal standard
code: design code or technical code
guideline: guideline or recommended practice
regulation: law or administrative regulation
technical_specification: port, interface, product, system, or engineering technical specification
report: institutional/technical report
dataset: structured dataset
spreadsheet: Excel/CSV spreadsheet
note: user note or internal memo
book: monograph or textbook
thesis: thesis/dissertation
web: website or online page
```

## Permission Rules

Default permission:

```json
{
  "A_core": {"cite_allowed": true, "reference_allowed": true},
  "B_background": {"cite_allowed": true, "reference_allowed": true},
  "C_method": {"cite_allowed": true, "reference_allowed": true},
  "D_internal": {"cite_allowed": false, "reference_allowed": false},
  "unclassified": {"cite_allowed": false, "reference_allowed": false}
}
```

If a D source is explicitly made citeable by the user, record the override:

```json
{
  "permission_override": true,
  "override_reason": "User confirmed this internal report is public and citeable."
}
```

## Ambiguity Handling

Set `source_class=unclassified` when:

- metadata is incomplete
- a patent/standard/technical specification might be either A or C
- a report might be public or internal
- a dataset might be citeable or private
- user intent is unclear

Show unclassified sources to the user before final ranking.

## Outputs

Confirmed classification record:

```json
{
  "source_id": "",
  "source_class": "C_method",
  "source_type": "technical_specification",
  "cite_allowed": true,
  "reference_allowed": true,
  "classification_confidence": 0.9,
  "classification_reason": "Technical specification supports method/evaluation criteria.",
  "classified_by": "agent",
  "user_confirmed": false
}
```

When user confirms:

```json
{
  "user_confirmed": true,
  "confirmed_at": "YYYY-MM-DD HH:mm:ss"
}
```

