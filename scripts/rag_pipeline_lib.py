from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any


DEFAULT_STATE = {
    "brief_status": "not_started",
    "source_screening_status": "not_started",
    "carding_status": "not_started",
    "query_plan_status": "not_started",
    "retrieval_status": "not_started",
    "section_draft_status": "not_started",
    "claim_check_status": "not_started",
    "citation_status": "not_started",
    "word_format_status": "not_required",
}


SECTION_PURPOSES = {
    "Introduction": [
        ("background", ["A_core", "B_background"], ["text", "citation", "result"], ["paper", "review", "report"]),
        ("research_gap", ["A_core", "B_background"], ["text", "result", "citation"], ["paper", "review"]),
        ("state_of_the_art", ["A_core", "B_background"], ["text", "result", "table"], ["paper", "review"]),
    ],
    "Method": [
        ("model_setup", ["C_method", "A_core"], ["method", "standard_clause", "equation"], ["paper", "standard", "code", "technical_specification"]),
        ("parameter_basis", ["C_method", "A_core"], ["method", "table", "data"], ["paper", "standard", "dataset"]),
        ("standard_code", ["C_method"], ["standard_clause", "method"], ["standard", "code", "guideline", "regulation", "technical_specification"]),
        ("formula_metric", ["C_method"], ["equation", "method"], ["paper", "standard", "code"]),
    ],
    "Results": [
        ("comparison", ["A_core", "C_method"], ["result", "table", "figure"], ["paper", "dataset", "spreadsheet"]),
        ("mechanism_explanation", ["A_core", "C_method"], ["result", "figure", "method"], ["paper", "report"]),
        ("failure_mode", ["A_core", "C_method"], ["result", "figure"], ["paper", "report"]),
    ],
    "Discussion": [
        ("limitation", ["A_core", "B_background", "C_method"], ["text", "result"], ["paper", "review", "report"]),
        ("contradiction", ["A_core", "B_background", "C_method"], ["result", "table", "citation"], ["paper", "review"]),
        ("engineering_implication", ["A_core", "C_method"], ["result", "standard_clause", "method"], ["paper", "standard", "code"]),
    ],
}


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")


def append_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_state(output_root: Path) -> dict:
    state = DEFAULT_STATE | read_json(output_root / "workflow_state.json", {})
    state["output_root"] = str(output_root)
    return state


def update_state(output_root: Path, **updates: str) -> dict:
    state = load_state(output_root)
    state.update(updates)
    write_json(output_root / "workflow_state.json", state)
    return state


def split_sections(value: str) -> list[str]:
    sections = [part.strip() for part in re.split(r"[,;，；]+", value or "") if part.strip()]
    return sections or ["Introduction", "Method", "Results", "Discussion"]


def build_query_plan(output_root: Path, title: str, sections: list[str], language: str = "zh", top_k: int = 12) -> dict:
    queries = []
    for section in sections:
        defaults = SECTION_PURPOSES.get(section, SECTION_PURPOSES.get(section.title(), []))
        for index, (purpose, classes, kinds, source_types) in enumerate(defaults, 1):
            query_text = f"{title} {section} {purpose}".strip()
            queries.append(
                {
                    "query_id": f"{section.lower()}_{purpose}_{index:03d}",
                    "section": section,
                    "section_purpose": purpose,
                    "query": query_text,
                    "allowed_source_class": classes,
                    "preferred_content_kind": kinds,
                    "preferred_source_type": source_types,
                    "top_k": top_k,
                    "notes": "",
                }
            )
    plan = {"article_id": "", "title": title, "language": language, "queries": queries}
    write_json(output_root / "queries" / "query_plan.json", plan)
    update_state(output_root, query_plan_status="ready")
    return plan


def load_cards(output_root: Path) -> list[dict]:
    cards = []
    for path in sorted((output_root / "cards").glob("*.jsonl")):
        cards.extend(read_jsonl(path))
    return cards


def tokenize(text: str) -> list[str]:
    lowered = (text or "").lower()
    ascii_tokens = re.findall(r"[a-z0-9_]+", lowered)
    cjk_tokens = re.findall(r"[\u3400-\u9fff]{2,}", lowered)
    chars = re.findall(r"[\u3400-\u9fff]", lowered)
    return ascii_tokens + cjk_tokens + chars


def card_text(card: dict) -> str:
    return " ".join(
        str(card.get(key, ""))
        for key in ("evidence_text", "section_path", "content_kind", "rhetorical_role", "source_type")
    )


def score_card(query: dict, card: dict) -> float:
    q_tokens = tokenize(query.get("query", ""))
    c_tokens = tokenize(card_text(card))
    if not c_tokens:
        return 0.0
    tf = sum(c_tokens.count(token) for token in q_tokens)
    score = float(tf)
    if card.get("content_kind") in set(query.get("preferred_content_kind") or []):
        score += 3.0
    if card.get("source_type") in set(query.get("preferred_source_type") or []):
        score += 1.0
    if query.get("section", "").lower() in str(card.get("section_path", "")).lower():
        score += 1.0
    if card.get("cite_allowed", True):
        score += 0.25
    return score


def retrieve_cards(output_root: Path) -> list[dict]:
    state = load_state(output_root)
    if state.get("carding_status") != "ready":
        raise SystemExit("carding_status is not ready")
    plan = read_json(output_root / "queries" / "query_plan.json", {"queries": []})
    cards = load_cards(output_root)
    traces = []
    for query in plan.get("queries", []):
        allowed = set(query.get("allowed_source_class") or [])
        preferred = set(query.get("preferred_content_kind") or [])
        filtered = [
            card
            for card in cards
            if (not allowed or card.get("source_class") in allowed)
            and (not preferred or card.get("content_kind") in preferred)
        ]
        ranked = sorted(
            (
                (score_card(query, card), card)
                for card in filtered
            ),
            key=lambda item: item[0],
            reverse=True,
        )
        results = []
        for rank, (score, card) in enumerate(ranked[: int(query.get("top_k") or 12)], 1):
            if score <= 0 and ranked[0][0] > 0:
                continue
            location = card.get("source_location") or {}
            page = location.get("page_start") or location.get("clause") or location.get("line_start") or ""
            results.append(
                {
                    "rank": rank,
                    "card_id": card.get("card_id", ""),
                    "source_id": card.get("source_id", ""),
                    "source_class": card.get("source_class", ""),
                    "source_type": card.get("source_type", ""),
                    "content_kind": card.get("content_kind", ""),
                    "score": round(float(score), 4),
                    "section_fit": query.get("section_purpose", ""),
                    "evidence_preview": str(card.get("evidence_text", ""))[:240],
                    "page_or_location": str(page),
                }
            )
        traces.append(
            {
                "query_id": query.get("query_id", ""),
                "section": query.get("section", ""),
                "section_purpose": query.get("section_purpose", ""),
                "query": query.get("query", ""),
                "retrieval_method": ["keyword", "metadata_filter", "section_purpose_rerank"],
                "filters": {
                    "allowed_source_class": query.get("allowed_source_class", []),
                    "preferred_content_kind": query.get("preferred_content_kind", []),
                    "preferred_source_type": query.get("preferred_source_type", []),
                },
                "top_k": int(query.get("top_k") or 12),
                "results": results,
            }
        )
    write_jsonl(output_root / "retrieval" / "retrieval_trace.jsonl", traces)
    update_state(output_root, retrieval_status="ready")
    return traces


def split_claims(text: str) -> list[str]:
    claims = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("Evidence used"):
            continue
        parts = [part.strip() for part in re.split(r"(?<=[。！？.!?])\s*", line) if part.strip()]
        claims.extend(parts)
    return claims


def extract_ref(text: str) -> tuple[str, str]:
    match = re.search(r"\[source_id:([^;\]]+);\s*card_id:([^\]]+)\]", text)
    if not match:
        return "", ""
    return match.group(1).strip(), match.group(2).strip()


def clean_claim(text: str) -> str:
    return re.sub(r"\s*\[source_id:[^\]]+\]", "", text).strip()


def claim_type(text: str, card: dict | None = None) -> str:
    source = f"{text} {card.get('content_kind', '') if card else ''}"
    if re.search(r"公式|计算|ratio|equation|阻尼比|面积", source, re.I):
        return "formula"
    if re.search(r"结果|承载力|提高|降低|对比|峰值|result", source, re.I):
        return "result"
    if re.search(r"方法|模型|设置|参数|method", source, re.I):
        return "method"
    return "fact"


def evidence_location(card: dict) -> str:
    loc = card.get("source_location") or {}
    for key in ("page_start", "clause", "line_start", "claim_number"):
        value = loc.get(key)
        if value not in (None, ""):
            return str(value)
    return ""


def check_claim_evidence(output_root: Path) -> dict[str, int]:
    cards = {card.get("card_id"): card for card in load_cards(output_root)}
    claim_records = []
    evidence_units = []
    claim_maps = []
    unsupported = []
    weak = []
    mismatch = []
    seen_evidence = set()
    claim_index = 0
    for draft in sorted((output_root / "draft_sections").glob("*.md")):
        section = draft.stem.rsplit("_v", 1)[0]
        for raw_claim in split_claims(draft.read_text(encoding="utf-8-sig")):
            claim_index += 1
            source_id, card_id = extract_ref(raw_claim)
            card = cards.get(card_id)
            ctype = claim_type(raw_claim, card)
            claim_id = f"claim_{claim_index:04d}"
            text = clean_claim(raw_claim)
            status = "supported" if card and source_id and card.get("source_id") == source_id else "unsupported"
            reason = ""
            if status == "supported" and ctype == "formula" and not (
                card.get("content_kind") == "equation" or card.get("source_class") == "C_method"
            ):
                status = "weak"
                reason = "formula claim lacks equation_card or C_method source"
            if status == "supported" and ctype == "result" and card.get("content_kind") not in {"result", "table", "figure"}:
                status = "weak"
                reason = "result claim lacks result/table/figure evidence"
            if status == "supported" and not evidence_location(card):
                status = "weak"
                reason = "missing page_or_location"
            claim_records.append(
                {
                    "claim_id": claim_id,
                    "section": section,
                    "claim_text": text,
                    "claim_type": ctype,
                    "importance": "key" if ctype in {"formula", "result"} else "normal",
                    "needs_citation": True,
                    "status": status,
                }
            )
            if card:
                evidence_id = card_id
                if evidence_id not in seen_evidence:
                    seen_evidence.add(evidence_id)
                    evidence_units.append(
                        {
                            "evidence_id": evidence_id,
                            "card_id": card_id,
                            "source_id": card.get("source_id", ""),
                            "source_class": card.get("source_class", ""),
                            "source_type": card.get("source_type", ""),
                            "content_kind": card.get("content_kind", ""),
                            "evidence_text": card.get("evidence_text", ""),
                            "page_or_location": evidence_location(card),
                            "cite_allowed": card.get("cite_allowed", True),
                            "reference_allowed": card.get("reference_allowed", True),
                        }
                    )
                support_level = "strong" if status == "supported" else "weak"
                claim_maps.append(
                    {
                        "claim_id": claim_id,
                        "evidence_id": evidence_id,
                        "support_level": support_level,
                        "citation_required": True,
                        "citation_key_or_number": "",
                        "notes": reason,
                    }
                )
                if card.get("source_id") != source_id:
                    mismatch.append(
                        {
                            "claim_id": claim_id,
                            "section": section,
                            "claim_text": text,
                            "citation_key_or_number": "",
                            "source_id": source_id,
                            "issue": "source_id does not match card source_id",
                            "suggested_action": "Correct source_id or card_id.",
                        }
                    )
            if status == "unsupported":
                unsupported.append(
                    {
                        "claim_id": claim_id,
                        "section": section,
                        "claim_text": text,
                        "claim_type": ctype,
                        "reason": "missing valid source_id/card_id",
                        "suggested_action": "Add evidence or remove/rewrite claim.",
                    }
                )
            elif status == "weak":
                weak.append(
                    {
                        "claim_id": claim_id,
                        "section": section,
                        "claim_text": text,
                        "evidence_id": card_id,
                        "support_level": "weak",
                        "weakness": reason or "weak evidence",
                        "suggested_action": "Find stronger evidence or soften claim.",
                    }
                )
    write_jsonl(output_root / "claims" / "claim_registry.jsonl", claim_records)
    write_jsonl(output_root / "claims" / "evidence_units.jsonl", evidence_units)
    write_jsonl(output_root / "claims" / "claim_evidence_map.jsonl", claim_maps)
    write_csv(output_root / "qa" / "unsupported_claims.csv", unsupported, ["claim_id", "section", "claim_text", "claim_type", "reason", "suggested_action"])
    write_csv(output_root / "qa" / "weak_evidence_claims.csv", weak, ["claim_id", "section", "claim_text", "evidence_id", "support_level", "weakness", "suggested_action"])
    write_csv(output_root / "qa" / "citation_mismatch.csv", mismatch, ["claim_id", "section", "claim_text", "citation_key_or_number", "source_id", "issue", "suggested_action"])
    update_state(output_root, claim_check_status="ready")
    return {"claims": len(claim_records), "unsupported": len(unsupported), "weak": len(weak)}


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9\u3400-\u9fff]+", "_", value.lower(), flags=re.I).strip("_")
    return text or "section"


def next_versioned_path(directory: Path, stem: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    version = 1
    while True:
        path = directory / f"{stem}_v{version}.md"
        if not path.exists():
            return path
        version += 1


def route_section_writing(output_root: Path, section: str) -> Path:
    state = load_state(output_root)
    if state.get("query_plan_status") != "ready":
        raise SystemExit("query_plan_status is not ready")
    if state.get("retrieval_status") != "ready":
        raise SystemExit("retrieval_status is not ready")
    traces = read_jsonl(output_root / "retrieval" / "retrieval_trace.jsonl")
    section_traces = [trace for trace in traces if str(trace.get("section", "")).lower() == section.lower()]
    draft_path = next_versioned_path(output_root / "draft_sections", slug(section))
    lines = [f"# {section}", ""]
    evidence_lines = []
    claim_index = 0
    for trace in section_traces:
        for result in trace.get("results", []):
            preview = str(result.get("evidence_preview", "")).strip()
            if not preview:
                continue
            claim_index += 1
            source_id = result.get("source_id", "")
            card_id = result.get("card_id", "")
            sentence = preview.rstrip("。.!?！？") + f"。[source_id:{source_id}; card_id:{card_id}]"
            lines.append(sentence)
            evidence_lines.extend(
                [
                    f"- claim_id: draft_claim_{claim_index:04d}",
                    f"  evidence_id: {card_id}",
                    f"  source_id: {source_id}",
                    f"  card_id: {card_id}",
                ]
            )
    if claim_index == 0:
        lines.append("本节尚无可用检索证据。")
    lines.extend(["", "Evidence used:", *evidence_lines])
    draft_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    update_state(output_root, section_draft_status="drafted")
    return draft_path
