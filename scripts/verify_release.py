from __future__ import annotations

import argparse
import py_compile
import re
from pathlib import Path


FORBIDDEN_PATTERNS = [
    ("absolute_windows_path", re.compile(r"\b[A-Z]:\\", re.IGNORECASE)),
    ("windows_user_profile", re.compile(r"\bUsers\\[^\\\s]+", re.IGNORECASE)),
    ("old_article_skill_name", re.compile("-".join(["article", "writing", "skill"]), re.IGNORECASE)),
    ("old_data_folder_name", re.compile("-".join(["uj", "data"]), re.IGNORECASE)),
    ("old_submit_data_path", re.compile(r"submit" + r"\\DATA", re.IGNORECASE)),
]


SCRIPT_PATHS = [
    "skills/article-rag-chunking/scripts/extract_metadata.py",
    "skills/article-rag-chunking/scripts/enrich_metadata.py",
    "skills/article-rag-chunking/scripts/generate_cards.py",
    "skills/article-rag-chunking/scripts/rank_sources.py",
    "skills/article-rag-chunking/scripts/run_rag_pipeline.py",
    "skills/word-formatting/scripts/inspect_docx.py",
    "skills/word-formatting/scripts/format_docx.py",
]


TEXT_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".py", ".txt", ".ps1"}


def scan_forbidden(root: Path) -> list[str]:
    findings = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        relative = path.relative_to(root)
        if ".local" in relative.parts:
            continue
        if path.name == "verify_release.py" and path.parent.name == "scripts":
            continue
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), 1):
            for label, regex in FORBIDDEN_PATTERNS:
                if regex.search(line):
                    findings.append(f"{relative}:{line_no}: forbidden pattern {label}: {line.strip()}")
    return findings


def compile_scripts(root: Path) -> list[str]:
    errors = []
    for script in SCRIPT_PATHS:
        path = root / script
        if not path.exists():
            errors.append(f"missing script: {script}")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append(f"compile failed: {script}: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify generic RAG writing skill release candidate.")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    root = args.root.resolve()
    findings = scan_forbidden(root)
    compile_errors = compile_scripts(root)
    for item in findings + compile_errors:
        print(item)
    if findings or compile_errors:
        return 1
    print(f"release candidate verification passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
