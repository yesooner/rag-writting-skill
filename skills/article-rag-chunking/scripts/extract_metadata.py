from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TEXT_EXTENSIONS = {".md", ".txt"}
JSON_EXTENSIONS = {".json"}


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"_json_error": str(exc)}
    return data if isinstance(data, dict) else {"raw_json": data}


def first_value(data: dict, keys: list[str], default=None):
    for key in keys:
        if key in data and data[key] not in (None, "", []):
            return data[key]
    return default


def normalize_authors(value):
    if value is None:
        return []
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                name = item.get("name") or " ".join(str(item.get(k, "")) for k in ("given", "family")).strip()
                if name:
                    out.append(name)
        return out
    if isinstance(value, str):
        return [part.strip() for part in re.split(r";|, and | and ", value) if part.strip()]
    return []


def infer_from_md(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = ""
    for line in lines[:80]:
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            break
    doi = ""
    doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", text)
    if doi_match:
        doi = doi_match.group(0).rstrip(".,;)")
    year = None
    year_match = re.search(r"\b(19|20)\d{2}\b", "\n".join(lines[:120]))
    if year_match:
        year = int(year_match.group(0))
    return {"title": title, "doi": doi, "year": year}


def make_source_id(path: Path, index: int) -> str:
    safe = re.sub(r"[^A-Za-z0-9]+", "_", path.stem).strip("_").lower()
    return safe or f"source_{index:03d}"


def merge_metadata(json_path: Path | None, md_path: Path | None, index: int) -> dict:
    raw = read_json(json_path) if json_path else {}
    md_meta = infer_from_md(md_path) if md_path else {}
    source_path = str(json_path or md_path or "")
    source_id = first_value(raw, ["source_id", "paper_id", "id"], make_source_id(json_path or md_path, index))
    source_type = first_value(raw, ["source_type", "itemType", "type"], "paper")
    source_class = first_value(raw, ["source_class", "sourceClass"], "unclassified")
    title = first_value(raw, ["title", "name"], md_meta.get("title", ""))
    authors = normalize_authors(first_value(raw, ["authors", "creators", "creator", "author"], []))
    year = first_value(raw, ["year", "date_year", "publicationYear"], md_meta.get("year"))
    doi = first_value(raw, ["doi", "DOI"], md_meta.get("doi", ""))
    journal = first_value(raw, ["journal", "publicationTitle", "container-title", "container_title"], "")
    standard_number = first_value(raw, ["standard_number", "standardNumber"], "")
    patent_number = first_value(raw, ["patent_number", "patentNumber", "publication_number"], "")
    citation_count = first_value(raw, ["citation_count", "cited_by_count", "citations"], None)
    user_priority = first_value(raw, ["user_priority", "priority"], None)
    missing = []
    for field, value in {
        "title": title,
        "year": year,
        "doi": doi,
        "journal": journal,
    }.items():
        if value in (None, "", []):
            missing.append(field)
    return {
        "source_id": source_id,
        "source_class": source_class,
        "source_type": source_type,
        "title": title,
        "authors": authors,
        "year": year,
        "journal": journal,
        "doi": doi,
        "standard_number": standard_number,
        "patent_number": patent_number,
        "citation_count": citation_count,
        "journal_metric": first_value(raw, ["journal_metric", "quartile", "impact_factor"], None),
        "user_priority": user_priority,
        "source_path": source_path,
        "metadata_source": {"local_json": bool(json_path), "markdown_inference": bool(md_path), "user_supplied": True},
        "metadata_confidence": 0.7 if title else 0.3,
        "missing_metadata": missing,
    }


def collect_pairs(input_dir: Path) -> list[tuple[Path | None, Path | None]]:
    jsons = {p.stem: p for p in input_dir.rglob("*") if p.suffix.lower() in JSON_EXTENSIONS}
    texts = {p.stem: p for p in input_dir.rglob("*") if p.suffix.lower() in TEXT_EXTENSIONS}
    stems = sorted(set(jsons) | set(texts))
    return [(jsons.get(stem), texts.get(stem)) for stem in stems]


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract local source metadata from JSON/Markdown files.")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    records = [merge_metadata(json_path, md_path, index + 1) for index, (json_path, md_path) in enumerate(collect_pairs(args.input_dir))]
    with args.output.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"wrote {len(records)} metadata records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
