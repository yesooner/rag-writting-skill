from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from rag_pipeline_lib import check_claim_evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Check manuscript claims against RAG evidence cards.")
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    summary = check_claim_evidence(args.output_root)
    print(f"checked {summary['claims']} claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
