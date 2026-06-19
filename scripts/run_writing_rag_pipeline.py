from __future__ import annotations

import argparse
from pathlib import Path

from rag_pipeline_lib import build_query_plan, check_claim_evidence, retrieve_cards, route_section_writing, split_sections


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the executable RAG writing pipeline stages.")
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--sections", default="Introduction,Method,Results,Discussion")
    parser.add_argument("--skip-section-draft", action="store_true")
    args = parser.parse_args()

    build_query_plan(args.output_root, args.title, split_sections(args.sections))
    retrieve_cards(args.output_root)
    if not args.skip_section_draft:
        for section in split_sections(args.sections):
            route_section_writing(args.output_root, section)
    check_claim_evidence(args.output_root)
    print("writing RAG pipeline complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
