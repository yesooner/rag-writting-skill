from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from rag_pipeline_lib import retrieve_cards


def main() -> int:
    parser = argparse.ArgumentParser(description="Retrieve evidence from typed RAG cards.")
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    traces = retrieve_cards(args.output_root)
    print(f"wrote {len(traces)} retrieval trace records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
