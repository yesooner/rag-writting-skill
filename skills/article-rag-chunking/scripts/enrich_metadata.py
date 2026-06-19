from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def cache_key(provider: str, query: str) -> str:
    return hashlib.sha256(f"{provider}:{query}".encode("utf-8")).hexdigest()


def cached_get(url: str, provider: str, query: str, cache_dir: Path, no_network: bool, rate_limit: float) -> dict | None:
    provider_dir = cache_dir / provider
    provider_dir.mkdir(parents=True, exist_ok=True)
    cache_file = provider_dir / f"{cache_key(provider, query)}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))
    if no_network:
        return None
    time.sleep(max(rate_limit, 0))
    request = urllib.request.Request(url, headers={"User-Agent": "article-rag-chunking/1.0 (metadata enrichment)"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"_lookup_error": str(exc)}
    cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def crossref_lookup(record: dict, cache_dir: Path, no_network: bool, rate_limit: float) -> dict:
    doi = (record.get("doi") or "").strip()
    title = (record.get("title") or "").strip()
    if doi:
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
        data = cached_get(url, "crossref", doi.lower(), cache_dir, no_network, rate_limit)
        method = "doi"
    elif title:
        query = urllib.parse.urlencode({"query.title": title, "rows": 1})
        url = "https://api.crossref.org/works?" + query
        data = cached_get(url, "crossref", title.lower(), cache_dir, no_network, rate_limit)
        method = "title"
    else:
        return {"matched": False, "reason": "no DOI or title"}
    if not data or data.get("_lookup_error"):
        return {"matched": False, "reason": data.get("_lookup_error") if data else "no data"}
    message = data.get("message", {})
    item = message if method == "doi" else (message.get("items") or [{}])[0]
    if not item:
        return {"matched": False, "reason": "empty result"}
    return {
        "matched": True,
        "match_method": method,
        "confidence": 1.0 if method == "doi" else 0.75,
        "title": (item.get("title") or [""])[0],
        "journal": (item.get("container-title") or [""])[0],
        "doi": item.get("DOI", ""),
        "publisher": item.get("publisher", ""),
        "year": ((item.get("published-print") or item.get("published-online") or item.get("issued") or {}).get("date-parts") or [[None]])[0][0],
    }


def openalex_lookup(record: dict, cache_dir: Path, no_network: bool, rate_limit: float) -> dict:
    doi = (record.get("doi") or "").strip()
    title = (record.get("title") or "").strip()
    if doi:
        query_id = "https://doi.org/" + doi.lower()
        url = "https://api.openalex.org/works/" + urllib.parse.quote(query_id, safe="")
        data = cached_get(url, "openalex", doi.lower(), cache_dir, no_network, rate_limit)
        method = "doi"
    elif title:
        query = urllib.parse.urlencode({"search": title, "per-page": 1})
        url = "https://api.openalex.org/works?" + query
        data = cached_get(url, "openalex", title.lower(), cache_dir, no_network, rate_limit)
        method = "title"
    else:
        return {"matched": False, "reason": "no DOI or title"}
    if not data or data.get("_lookup_error"):
        return {"matched": False, "reason": data.get("_lookup_error") if data else "no data"}
    item = data if method == "doi" else (data.get("results") or [{}])[0]
    if not item:
        return {"matched": False, "reason": "empty result"}
    host = item.get("primary_location", {}).get("source") or {}
    return {
        "matched": True,
        "match_method": method,
        "confidence": 1.0 if method == "doi" else 0.75,
        "citation_count": item.get("cited_by_count"),
        "journal": host.get("display_name", ""),
        "journal_issn": host.get("issn_l", ""),
        "year": item.get("publication_year"),
        "openalex_id": item.get("id", ""),
    }


def merge_enrichment(record: dict, provider: str, result: dict) -> None:
    record.setdefault("external_metadata", {})[provider] = result
    if not result.get("matched"):
        return
    if provider == "crossref":
        for field in ("title", "journal", "doi", "year"):
            if not record.get(field) and result.get(field):
                record[field] = result[field]
    if provider == "openalex":
        if record.get("citation_count") is None and result.get("citation_count") is not None:
            record["citation_count"] = result["citation_count"]
        if not record.get("journal") and result.get("journal"):
            record["journal"] = result["journal"]
        if not record.get("year") and result.get("year"):
            record["year"] = result["year"]


def update_missing(record: dict) -> None:
    missing = []
    for field in ("title", "year", "doi", "journal", "citation_count"):
        if record.get(field) in (None, "", []):
            missing.append(field)
    record["missing_metadata"] = missing
    matched = [v for v in record.get("external_metadata", {}).values() if v.get("matched")]
    record["metadata_confidence"] = max([record.get("metadata_confidence") or 0.0] + [v.get("confidence", 0.0) for v in matched])


def main() -> int:
    parser = argparse.ArgumentParser(description="Optionally enrich source metadata with external providers.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--providers", default="crossref,openalex")
    parser.add_argument("--cache", required=True, type=Path)
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--rate-limit", type=float, default=1.0)
    args = parser.parse_args()

    providers = {part.strip().lower() for part in args.providers.split(",") if part.strip()}
    records = read_jsonl(args.input)
    for record in records:
        record.setdefault("metadata_source", {})["local_json"] = bool(record.get("metadata_source", {}).get("local_json"))
        if "crossref" in providers:
            result = crossref_lookup(record, args.cache, args.no_network, args.rate_limit)
            merge_enrichment(record, "crossref", result)
            record.setdefault("metadata_source", {})["crossref"] = bool(result.get("matched"))
        if "openalex" in providers:
            result = openalex_lookup(record, args.cache, args.no_network, args.rate_limit)
            merge_enrichment(record, "openalex", result)
            record.setdefault("metadata_source", {})["openalex"] = bool(result.get("matched"))
        update_missing(record)
    write_jsonl(args.output, records)
    print(f"wrote {len(records)} enriched metadata records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

