from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


TEXT_EXTENSIONS = {".md", ".txt"}
JSON_EXTENSIONS = {".json"}
STRUCTURE_KEYS = ("blocks", "sections", "pages", "elements", "chunks", "cards", "items")


def read_jsonl(path: Path) -> list[dict]:
    records = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def collect_by_stem(input_dir: Path, extensions: set[str]) -> dict[str, Path]:
    return {p.stem.lower(): p for p in input_dir.rglob("*") if p.suffix.lower() in extensions}


def source_key(path: Path) -> str:
    return re.sub(r"[^a-z0-9]+", "_", path.stem.lower()).strip("_")


def stable_id(*parts: str) -> str:
    raw = "::".join(parts).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:12]


def has_cardable_json_content(data: Any) -> bool:
    if isinstance(data, list):
        return any(has_cardable_json_content(item) for item in data)
    if not isinstance(data, dict):
        return False
    if any(key in data for key in STRUCTURE_KEYS):
        return True
    content_keys = ("text", "content", "markdown", "caption", "latex", "formula", "abstract", "table", "rows")
    return any(data.get(key) not in (None, "", []) for key in content_keys)


def is_cardable_json(path: Path) -> bool:
    try:
        return has_cardable_json_content(read_json(path))
    except Exception:
        return False


def split_markdown_blocks(text: str) -> list[dict]:
    lines = text.splitlines()
    blocks = []
    section_stack: list[str] = []
    buffer: list[str] = []
    buffer_start = 1
    in_fence = False
    fence_lang = ""

    def flush(end_line: int) -> None:
        nonlocal buffer, buffer_start
        content = "\n".join(buffer).strip()
        if content:
            blocks.extend(classify_text_block(content, buffer_start, end_line, section_stack))
        buffer = []
        buffer_start = end_line + 1

    for line_no, line in enumerate(lines, 1):
        stripped = line.strip()
        fence_match = re.match(r"^```(.*)$", stripped)
        if fence_match:
            if not in_fence:
                flush(line_no - 1)
                in_fence = True
                fence_lang = fence_match.group(1).strip().lower()
                buffer_start = line_no
                buffer = [line]
            else:
                buffer.append(line)
                content = "\n".join(buffer)
                kind = "equation" if fence_lang in {"math", "latex", "tex"} else "text"
                blocks.append(make_block(content, kind, buffer_start, line_no, section_stack))
                buffer = []
                buffer_start = line_no + 1
                in_fence = False
                fence_lang = ""
            continue
        if in_fence:
            buffer.append(line)
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush(line_no - 1)
            level = len(heading.group(1))
            title = heading.group(2).strip()
            section_stack = section_stack[: level - 1] + [title]
            blocks.append(make_block(title, "section", line_no, line_no, section_stack))
            buffer_start = line_no + 1
            continue

        if not buffer:
            buffer_start = line_no
        buffer.append(line)

        if not stripped:
            flush(line_no)

    flush(len(lines))
    return blocks


def classify_text_block(content: str, start: int, end: int, section_stack: list[str]) -> list[dict]:
    stripped = content.strip()
    if not stripped:
        return []
    image_matches = list(re.finditer(r"!\[[^\]]*\]\([^)]+\)", stripped))
    if image_matches and len(stripped.splitlines()) <= 4:
        return [make_block(stripped, "figure", start, end, section_stack)]
    if looks_like_table(stripped):
        return [make_block(stripped, "table", start, end, section_stack)]
    if looks_like_equation(stripped):
        return [make_block(stripped, "equation", start, end, section_stack)]
    if looks_like_data(stripped):
        return [make_block(stripped, "data", start, end, section_stack)]
    return [make_block(stripped, "text", start, end, section_stack)]


def looks_like_table(text: str) -> bool:
    lines = [line for line in text.splitlines() if line.strip()]
    return len(lines) >= 2 and any("|" in line for line in lines) and any(re.search(r"\|\s*:?-{3,}:?\s*\|", line) for line in lines)


def looks_like_equation(text: str) -> bool:
    if text.startswith("$$") and text.endswith("$$"):
        return True
    if re.search(r"\\begin\{equation\}|\\\(|\\\[", text):
        return True
    return False


def looks_like_data(text: str) -> bool:
    if re.search(r"\b(data|dataset|workbook|sheet|excel|csv|xlsx|xls)\b", text, flags=re.I):
        return True
    numeric_tokens = re.findall(r"[-+]?\d+(?:\.\d+)?\s*(?:%|kN|MPa|mm|J|N/mm)?", text)
    return len(numeric_tokens) >= 8


def normalize_kind(value: str, content: str = "") -> str:
    raw = (value or "").strip().lower()
    mapping = {
        "heading": "section",
        "header": "section",
        "section_title": "section",
        "paragraph": "text",
        "para": "text",
        "body": "text",
        "image": "figure",
        "fig": "figure",
        "picture": "figure",
        "formula": "equation",
        "math": "equation",
        "latex": "equation",
        "tabular": "table",
        "dataset": "data",
        "spreadsheet": "data",
        "standard": "standard_clause",
        "clause": "standard_clause",
        "patent": "patent_claim",
        "claim": "patent_claim",
    }
    kind = mapping.get(raw, raw)
    allowed = {
        "section",
        "text",
        "table",
        "figure",
        "equation",
        "data",
        "term",
        "citation",
        "standard_clause",
        "patent_claim",
        "method",
        "result",
    }
    if kind in allowed:
        return kind
    if looks_like_table(content):
        return "table"
    if looks_like_equation(content):
        return "equation"
    if looks_like_data(content):
        return "data"
    return "text"


def card_type_for(content_kind: str) -> str:
    return {
        "section": "section_card",
        "text": "section_card",
        "table": "table_card",
        "figure": "figure_card",
        "equation": "equation_card",
        "data": "data_card",
        "term": "term_card",
        "citation": "citation_card",
        "standard_clause": "standard_card",
        "patent_claim": "patent_card",
        "method": "method_card",
        "result": "result_card",
    }.get(content_kind, "section_card")


def make_block(content: str, content_kind: str, start: int | None, end: int | None, section_stack: list[str], page: int | None = None) -> dict:
    kind = normalize_kind(content_kind, content)
    return {
        "content_kind": kind,
        "card_type": card_type_for(kind),
        "section_path": " > ".join(section_stack),
        "line_start": start,
        "line_end": end,
        "page_start": page,
        "page_end": page,
        "content": content,
    }


def json_content_from_item(item: dict) -> tuple[str, str]:
    content = (
        item.get("text")
        or item.get("content")
        or item.get("markdown")
        or item.get("caption")
        or item.get("latex")
        or item.get("formula")
        or item.get("html")
        or item.get("abstract")
        or ""
    )
    if not content and (item.get("table") is not None or item.get("rows") is not None):
        content = json.dumps(item.get("table", item.get("rows")), ensure_ascii=False)
    if not content and (item.get("image_path") or item.get("img_path") or item.get("path")):
        content = " ".join(str(item.get(k, "")) for k in ("image_path", "img_path", "path", "caption") if item.get(k))
    kind = (
        item.get("content_kind")
        or item.get("card_type")
        or item.get("type")
        or item.get("category")
        or item.get("block_type")
        or item.get("role")
        or ""
    )
    return str(content), str(kind)


def section_stack_from_item(item: dict, current_stack: list[str]) -> list[str]:
    section = item.get("section_path") or item.get("section") or item.get("heading") or item.get("title_path")
    if isinstance(section, list):
        return [str(part) for part in section if str(part).strip()]
    if isinstance(section, str) and section.strip():
        return [part.strip() for part in re.split(r">|/|\\\\", section) if part.strip()]
    title = item.get("title")
    kind = normalize_kind(str(item.get("type") or item.get("content_kind") or ""), str(title or ""))
    if kind == "section" and title:
        return current_stack + [str(title)]
    return current_stack


def flatten_json_blocks(data: Any, section_stack: list[str] | None = None) -> list[dict]:
    section_stack = section_stack or []
    blocks: list[dict] = []

    if isinstance(data, list):
        for item in data:
            blocks.extend(flatten_json_blocks(item, section_stack))
        return blocks

    if not isinstance(data, dict):
        if str(data).strip():
            return [make_block(str(data), "text", None, None, section_stack)]
        return []

    local_stack = section_stack_from_item(data, section_stack)
    content, kind = json_content_from_item(data)
    if content.strip():
        blocks.append(
            make_block(
                content.strip(),
                kind,
                data.get("line_start") or data.get("start_line"),
                data.get("line_end") or data.get("end_line"),
                local_stack,
                data.get("page") or data.get("page_num") or data.get("page_number"),
            )
        )

    for key in STRUCTURE_KEYS:
        value = data.get(key)
        if value is not None:
            blocks.extend(flatten_json_blocks(value, local_stack))
    return blocks


def infer_role(block: dict) -> str:
    section = (block.get("section_path") or "").lower()
    kind = block.get("content_kind")
    if kind == "equation":
        return "method"
    if kind == "figure":
        return "result"
    if kind == "table":
        return "comparison"
    if kind == "data":
        return "data_trace"
    if kind == "standard_clause":
        return "standard_clause"
    if kind == "patent_claim":
        return "patent_claim"
    if any(key in section for key in ("method", "model", "方法", "模型", "试验", "实验")):
        return "method"
    if any(key in section for key in ("result", "discussion", "结果", "分析", "讨论")):
        return "result"
    if any(key in section for key in ("background", "review", "背景", "综述")):
        return "background"
    return "citation_support"


def find_source_file(record: dict, texts: dict[str, Path], jsons: dict[str, Path]) -> tuple[Path | None, str]:
    source_id = (record.get("source_id") or "").lower()
    source_path_key = source_key(Path(record.get("source_path") or source_id))
    candidates = [source_id, source_path_key]
    for key in candidates:
        if key in jsons and is_cardable_json(jsons[key]):
            return jsons[key], "json"
    for key in candidates:
        if key in texts:
            return texts[key], "text"
    return None, ""


def blocks_from_source(path: Path, source_format: str) -> list[dict]:
    if source_format == "json":
        data = read_json(path)
        blocks = flatten_json_blocks(data)
        if blocks:
            return blocks
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    return split_markdown_blocks(text)


def build_cards(input_dir: Path, metadata_path: Path, output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    records = read_jsonl(metadata_path)
    texts = collect_by_stem(input_dir, TEXT_EXTENSIONS)
    jsons = collect_by_stem(input_dir, JSON_EXTENSIONS)
    total = 0
    for record in records:
        source_id = record.get("source_id") or ""
        source_path, source_format = find_source_file(record, texts, jsons)
        if not source_path:
            continue
        blocks = blocks_from_source(source_path, source_format)
        output_path = output_dir / f"{source_id}.jsonl"
        with output_path.open("w", encoding="utf-8") as handle:
            for index, block in enumerate(blocks, 1):
                content = block.pop("content")
                role = infer_role(block)
                card = {
                    "card_id": f"{source_id}_{index:04d}_{stable_id(source_id, str(index), content)}",
                    "source_id": source_id,
                    "source_class": record.get("source_class", "unclassified"),
                    "source_type": record.get("source_type", ""),
                    "card_type": block["card_type"],
                    "content_kind": block["content_kind"],
                    "title": record.get("title", ""),
                    "section_path": block["section_path"],
                    "source_location": {
                        "page_start": block.get("page_start"),
                        "page_end": block.get("page_end"),
                        "line_start": block.get("line_start"),
                        "line_end": block.get("line_end"),
                        "clause": "",
                        "claim_number": "",
                    },
                    "claim": "",
                    "evidence_text": content,
                    "keywords": [],
                    "terms_en": [],
                    "terms_zh": [],
                    "preferred_translation": {},
                    "rhetorical_role": role,
                    "retrieval_triggers": [block["content_kind"], role],
                    "cite_allowed": record.get("cite_allowed", True),
                    "reference_allowed": record.get("reference_allowed", True),
                    "default_card_priority": 0.0,
                    "confirmed_card_priority": None,
                }
                handle.write(json.dumps(card, ensure_ascii=False) + "\n")
                total += 1
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate retrieval cards from JSON, Markdown, or Text sources.")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    count = build_cards(args.input_dir, args.metadata, args.output_dir)
    print(f"wrote {count} cards to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
