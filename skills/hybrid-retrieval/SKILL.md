---
name: hybrid-retrieval
description: Retrieve evidence from RAG cards using keyword, dense, source-class, content-kind, and section-purpose filters. Use when Claude Code needs to run or describe hybrid retrieval from typed article cards and write retrieval traces before section drafting or claim checking.
---

# Hybrid Retrieval

## Purpose

Use this skill after `query-planner` and after RAG cards exist. It retrieves candidate evidence cards and writes an auditable trace for each query.

## Required Inputs

Read:

```text
<output_root>/workflow_state.json
<output_root>/queries/query_plan.json
<output_root>/cards/*.jsonl
```

If cards are not ready, stop and route to `article-rag-chunking`.

## Retrieval Request

Each retrieval request should use:

```json
{
  "query": "equivalent viscous damping ratio calculation formula",
  "section": "Results",
  "allowed_source_class": ["A_core", "C_method"],
  "preferred_content_kind": ["equation", "result", "method"],
  "top_k": 12
}
```

## Strategy

Use the best available local retrieval implementation. If no dedicated retriever exists, perform a transparent fallback with keyword matching and metadata filters.

Recommended ranking stack:

```text
BM25 keyword retrieval
+ embedding dense retrieval when available
+ source_class filter
+ content_kind filter
+ preferred_source_type filter
+ rerank by section purpose
+ rerank by citation permission and evidence specificity
```

## Outputs

Append one JSON object per query to:

```text
<output_root>/retrieval/retrieval_trace.jsonl
```

Update:

```text
<output_root>/workflow_state.json
```

Set:

```json
{
  "retrieval_status": "ready"
}
```

## Script

Use the bundled keyword/metadata retriever when no external retrieval service is configured:

```powershell
python -X utf8 skills\hybrid-retrieval\scripts\retrieve_cards.py `
  --output-root "<output_root>"
```

## Trace Schema

```json
{
  "query_id": "",
  "section": "",
  "section_purpose": "",
  "query": "",
  "retrieval_method": ["bm25", "dense", "metadata_filter", "rerank"],
  "filters": {
    "allowed_source_class": [],
    "preferred_content_kind": [],
    "preferred_source_type": []
  },
  "top_k": 12,
  "results": [
    {
      "rank": 1,
      "card_id": "",
      "source_id": "",
      "source_class": "",
      "source_type": "",
      "content_kind": "",
      "score": 0.0,
      "section_fit": "",
      "evidence_preview": "",
      "page_or_location": ""
    }
  ]
}
```

## Hard Rules

- Do not invent retrieved cards.
- Do not use `D_internal` in public-facing prose unless the user explicitly permits it.
- Do not treat retrieval as evidence validation; run `claim-evidence-checker` after drafting.
- Always write `retrieval_trace.jsonl`; chat-only retrieval summaries are not enough.
