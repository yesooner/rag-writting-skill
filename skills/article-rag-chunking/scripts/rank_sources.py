from __future__ import annotations

import argparse
import json
from pathlib import Path


CLASS_ORDER = ["A_core", "B_background", "C_method", "D_internal", "unclassified"]


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def authority_label(record: dict) -> str:
    if record.get("citation_count") is not None:
        return f"citation={record['citation_count']}"
    if record.get("standard_number"):
        return "standard/code"
    if record.get("patent_number"):
        return "patent"
    metric = record.get("journal_metric")
    if metric:
        return str(metric)
    return "unknown"


def id_label(record: dict) -> str:
    return record.get("doi") or record.get("patent_number") or record.get("standard_number") or ""


def rank_score(record: dict) -> float:
    score = 0.0
    if record.get("user_priority") is not None:
        try:
            score += max(0, 100 - float(record["user_priority"]))
        except Exception:
            pass
    if record.get("year"):
        try:
            score += (float(record["year"]) - 1900) / 10
        except Exception:
            pass
    if record.get("citation_count") is not None:
        try:
            score += min(float(record["citation_count"]), 500) / 10
        except Exception:
            pass
    score += float(record.get("metadata_confidence") or 0) * 10
    if record.get("doi"):
        score += 5
    return score


def reason(record: dict) -> str:
    parts = []
    if record.get("user_priority") is not None:
        parts.append(f"user_priority={record['user_priority']}")
    if record.get("doi"):
        parts.append("DOI present")
    if record.get("citation_count") is not None:
        parts.append(f"citation={record['citation_count']}")
    if record.get("year"):
        parts.append(f"year={record['year']}")
    if record.get("patent_number"):
        parts.append("patent source")
    if record.get("standard_number"):
        parts.append("standard/code source")
    return "; ".join(parts) or "metadata-based default"


def render_group(class_name: str, records: list[dict]) -> str:
    titles = {
        "A_core": "A_core: 核心证据来源",
        "B_background": "B_background: 背景与综述来源",
        "C_method": "C_method: 方法、规范与指标来源",
        "D_internal": "D_internal: 内部资料与项目数据",
        "unclassified": "unclassified: 待用户确认分类",
    }
    lines = [f"## {titles.get(class_name, class_name)}", ""]
    lines.append("| 组内默认排序 | source_type | source_id | 标题 | 年份/版本 | DOI/专利号/标准号 | 引用量/权威性 | 元数据来源 | 默认分数 | 排序理由 | 用户确认组内排序 |")
    lines.append("|---:|---|---|---|---|---|---|---|---:|---|---:|")
    for index, record in enumerate(records, 1):
        record["default_rank_in_class"] = index
        record["confirmed_rank_in_class"] = None
        record["rank_confirmed_by_user"] = False
        record["rank_reason"] = reason(record)
        metadata_sources = ",".join(k for k, v in (record.get("metadata_source") or {}).items() if v) or "unknown"
        lines.append(
            "| {rank} | {stype} | {sid} | {title} | {year} | {idv} | {auth} | {msrc} | {score:.2f} | {reason} |  |".format(
                rank=index,
                stype=record.get("source_type", ""),
                sid=record.get("source_id", ""),
                title=(record.get("title") or "").replace("|", "\\|"),
                year=record.get("year") or "",
                idv=id_label(record).replace("|", "\\|"),
                auth=authority_label(record).replace("|", "\\|"),
                msrc=metadata_sources,
                score=record.get("_rank_score", 0.0),
                reason=record["rank_reason"].replace("|", "\\|"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ABCD-grouped default source ranking table for user confirmation.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--ranking-md", required=True, type=Path, help="User-confirmed local path for the ranking Markdown table.")
    parser.add_argument("--ranking-json", type=Path, help="Optional JSON output with default ranks only; not confirmed ranks.")
    args = parser.parse_args()

    records = read_jsonl(args.input)
    grouped: dict[str, list[dict]] = {name: [] for name in CLASS_ORDER}
    for record in records:
        class_name = record.get("source_class") or "unclassified"
        if class_name not in grouped:
            class_name = "unclassified"
            record["source_class"] = class_name
        record["_rank_score"] = rank_score(record)
        grouped[class_name].append(record)
    for records_in_class in grouped.values():
        records_in_class.sort(key=lambda item: item.get("_rank_score", 0), reverse=True)

    args.ranking_md.parent.mkdir(parents=True, exist_ok=True)
    sections = [
        "# Default Source Ranking For User Confirmation",
        "",
        "默认排序仅为建议。请在每个 source_class 内确认或调整顺序；未确认前不得写入 confirmed_rank_in_class。",
        "",
    ]
    for class_name in CLASS_ORDER:
        sections.append(render_group(class_name, grouped.get(class_name, [])))
    args.ranking_md.write_text("\n".join(sections), encoding="utf-8")
    if args.ranking_json:
        args.ranking_json.parent.mkdir(parents=True, exist_ok=True)
        flat = [record for class_name in CLASS_ORDER for record in grouped.get(class_name, [])]
        args.ranking_json.write_text(json.dumps(flat, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote ranking table to {args.ranking_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
