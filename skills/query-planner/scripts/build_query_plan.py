from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from rag_pipeline_lib import build_query_plan, split_sections


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a section-level RAG query plan.")
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--sections", default="Introduction,Method,Results,Discussion")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--top-k", type=int, default=12)
    args = parser.parse_args()
    plan = build_query_plan(args.output_root, args.title, split_sections(args.sections), args.language, args.top_k)
    print(f"wrote {len(plan['queries'])} queries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
