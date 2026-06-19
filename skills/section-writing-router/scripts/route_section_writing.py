from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from rag_pipeline_lib import route_section_writing


def main() -> int:
    parser = argparse.ArgumentParser(description="Draft a manuscript section from retrieval traces.")
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--section", required=True)
    args = parser.parse_args()
    path = route_section_writing(args.output_root, args.section)
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
