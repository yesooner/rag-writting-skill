from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def ensure_inside_output_root(path: Path, output_root: Path) -> Path:
    resolved = path.resolve()
    root = output_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"output path must stay inside output_root: {resolved}")
    return resolved


def run_step(args: list[str], log: list[dict]) -> None:
    started = datetime.now().isoformat(timespec="seconds")
    completed = subprocess.run(args, text=True, capture_output=True, encoding="utf-8")
    entry = {
        "command": args,
        "started_at": started,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    log.append(entry)
    if completed.returncode != 0:
        raise RuntimeError(f"pipeline step failed: {' '.join(args)}\n{completed.stderr}")


def write_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the article RAG preparation pipeline under a confirmed output_root.")
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--providers", default="crossref,openalex")
    parser.add_argument("--no-network", action="store_true")
    parser.add_argument("--skip-enrich", action="store_true")
    parser.add_argument("--python", default=sys.executable, help="Python executable used to run pipeline scripts.")
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    output_root = args.output_root.resolve()
    if not input_dir.exists():
        raise FileNotFoundError(f"input_dir does not exist: {input_dir}")

    cleaned_dir = ensure_inside_output_root(output_root / "cleaned", output_root)
    metadata_dir = ensure_inside_output_root(output_root / "metadata", output_root)
    cards_dir = ensure_inside_output_root(output_root / "cards", output_root)
    ranking_dir = ensure_inside_output_root(output_root / "ranking", output_root)
    logs_dir = ensure_inside_output_root(output_root / "logs", output_root)
    for directory in (cleaned_dir, metadata_dir, cards_dir, ranking_dir, logs_dir):
        directory.mkdir(parents=True, exist_ok=True)

    metadata_raw = metadata_dir / "metadata_raw.jsonl"
    metadata_enriched = metadata_dir / "metadata_enriched.jsonl"
    metadata_for_downstream = metadata_enriched if not args.skip_enrich else metadata_raw
    ranking_md = ranking_dir / "default_source_ranking.md"
    ranking_json = ranking_dir / "default_source_ranking.json"
    manifest = output_root / "rag_pipeline_manifest.json"
    step_log: list[dict] = []

    run_step(
        [
            args.python,
            "-X",
            "utf8",
            str(SCRIPT_DIR / "extract_metadata.py"),
            "--input-dir",
            str(input_dir),
            "--output",
            str(metadata_raw),
        ],
        step_log,
    )

    if not args.skip_enrich:
        enrich_cmd = [
            args.python,
            "-X",
            "utf8",
            str(SCRIPT_DIR / "enrich_metadata.py"),
            "--input",
            str(metadata_raw),
            "--output",
            str(metadata_enriched),
            "--providers",
            args.providers,
            "--cache",
            str(metadata_dir / "cache"),
        ]
        if args.no_network:
            enrich_cmd.append("--no-network")
        run_step(enrich_cmd, step_log)

    run_step(
        [
            args.python,
            "-X",
            "utf8",
            str(SCRIPT_DIR / "generate_cards.py"),
            "--input-dir",
            str(input_dir),
            "--metadata",
            str(metadata_for_downstream),
            "--output-dir",
            str(cards_dir),
        ],
        step_log,
    )

    run_step(
        [
            args.python,
            "-X",
            "utf8",
            str(SCRIPT_DIR / "rank_sources.py"),
            "--input",
            str(metadata_for_downstream),
            "--ranking-md",
            str(ranking_md),
            "--ranking-json",
            str(ranking_json),
        ],
        step_log,
    )

    write_json(logs_dir / "pipeline_steps.json", step_log)
    write_json(
        manifest,
        {
            "input_dir": str(input_dir),
            "output_root": str(output_root),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "metadata_raw": str(metadata_raw),
            "metadata_enriched": str(metadata_enriched) if not args.skip_enrich else None,
            "cards_dir": str(cards_dir),
            "default_ranking_md": str(ranking_md),
            "default_ranking_json": str(ranking_json),
            "confirmed_ranking_required": True,
        },
    )
    print(f"pipeline complete under {output_root}")
    print(f"ranking table requires user confirmation: {ranking_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
