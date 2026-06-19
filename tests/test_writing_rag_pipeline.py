from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(ROOT / script), *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_cards(output_root: Path) -> None:
    cards = [
        {
            "card_id": "card_eq_1",
            "source_id": "method_001",
            "source_class": "C_method",
            "source_type": "paper",
            "content_kind": "equation",
            "card_type": "equation_card",
            "section_path": "Method",
            "evidence_text": "等效黏滞阻尼比按耗能面积与弹性势能之比计算。",
            "retrieval_triggers": ["formula_metric", "method"],
            "rhetorical_role": "method",
            "cite_allowed": True,
            "reference_allowed": True,
            "source_location": {"page_start": 8, "line_start": 20},
        },
        {
            "card_id": "card_result_1",
            "source_id": "core_001",
            "source_class": "A_core",
            "source_type": "paper",
            "content_kind": "result",
            "card_type": "result_card",
            "section_path": "Results",
            "evidence_text": "试件 UJ-1 的峰值承载力高于 RC，对比结果表明界面构造提高了承载能力。",
            "retrieval_triggers": ["comparison", "result"],
            "rhetorical_role": "result",
            "cite_allowed": True,
            "reference_allowed": True,
            "source_location": {"page_start": 12, "line_start": 3},
        },
        {
            "card_id": "card_internal_1",
            "source_id": "internal_001",
            "source_class": "D_internal",
            "source_type": "dataset",
            "content_kind": "data",
            "card_type": "data_card",
            "section_path": "Results",
            "evidence_text": "内部表格显示 UJ-1 峰值承载力提高。",
            "retrieval_triggers": ["comparison", "data_trace"],
            "rhetorical_role": "data_trace",
            "cite_allowed": False,
            "reference_allowed": False,
            "source_location": {"page_start": None, "line_start": None},
        },
    ]
    write_jsonl(output_root / "cards" / "cards.jsonl", cards)
    (output_root / "workflow_state.json").write_text(
        json.dumps({"carding_status": "ready"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


class WritingRagPipelineTests(unittest.TestCase):
    def test_query_planner_writes_section_queries_and_updates_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "out"
            output_root.mkdir()
            (output_root / "workflow_state.json").write_text("{}", encoding="utf-8")

            run_script(
                "skills/query-planner/scripts/build_query_plan.py",
                "--output-root",
                str(output_root),
                "--title",
                "装配式结构抗震性能研究",
                "--sections",
                "Introduction,Method,Results,Discussion",
            )

            plan = json.loads((output_root / "queries" / "query_plan.json").read_text(encoding="utf-8"))
            purposes = {(item["section"], item["section_purpose"]) for item in plan["queries"]}
            self.assertIn(("Introduction", "background"), purposes)
            self.assertIn(("Method", "formula_metric"), purposes)
            self.assertIn(("Results", "comparison"), purposes)
            self.assertIn(("Discussion", "limitation"), purposes)
            self.assertTrue(all(item["allowed_source_class"] for item in plan["queries"]))
            state = json.loads((output_root / "workflow_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["query_plan_status"], "ready")

    def test_hybrid_retrieval_filters_cards_and_writes_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "out"
            output_root.mkdir()
            make_cards(output_root)
            (output_root / "queries").mkdir()
            (output_root / "queries" / "query_plan.json").write_text(
                json.dumps(
                    {
                        "queries": [
                            {
                                "query_id": "results_comparison_001",
                                "section": "Results",
                                "section_purpose": "comparison",
                                "query": "峰值承载力 对比 UJ RC",
                                "allowed_source_class": ["A_core"],
                                "preferred_content_kind": ["result", "table", "figure"],
                                "top_k": 5,
                            }
                        ]
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            run_script("skills/hybrid-retrieval/scripts/retrieve_cards.py", "--output-root", str(output_root))

            trace = read_jsonl(output_root / "retrieval" / "retrieval_trace.jsonl")
            self.assertEqual(trace[0]["query_id"], "results_comparison_001")
            self.assertEqual(trace[0]["results"][0]["card_id"], "card_result_1")
            self.assertTrue(all(result["source_class"] == "A_core" for result in trace[0]["results"]))
            state = json.loads((output_root / "workflow_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["retrieval_status"], "ready")

    def test_claim_evidence_checker_writes_claim_maps_and_qa(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "out"
            output_root.mkdir()
            make_cards(output_root)
            draft_dir = output_root / "draft_sections"
            draft_dir.mkdir()
            (draft_dir / "results_v1.md").write_text(
                "\n".join(
                    [
                        "UJ-1 的峰值承载力高于 RC。[source_id:core_001; card_id:card_result_1]",
                        "等效黏滞阻尼比采用面积比方法计算。[source_id:method_001; card_id:card_eq_1]",
                        "该构造一定可以适用于所有工程。",
                    ]
                ),
                encoding="utf-8",
            )

            run_script("skills/claim-evidence-checker/scripts/check_claim_evidence.py", "--output-root", str(output_root))

            claims = read_jsonl(output_root / "claims" / "claim_registry.jsonl")
            maps = read_jsonl(output_root / "claims" / "claim_evidence_map.jsonl")
            with (output_root / "qa" / "unsupported_claims.csv").open(encoding="utf-8") as handle:
                unsupported_rows = list(csv.DictReader(handle))
            self.assertTrue(any(claim["status"] == "supported" for claim in claims))
            self.assertTrue(any(item["evidence_id"] == "card_result_1" for item in maps))
            self.assertTrue(any("所有工程" in row["claim_text"] for row in unsupported_rows))
            state = json.loads((output_root / "workflow_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["claim_check_status"], "ready")

    def test_controller_runs_query_retrieval_and_claim_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "out"
            output_root.mkdir()
            make_cards(output_root)

            run_script(
                "scripts/run_writing_rag_pipeline.py",
                "--output-root",
                str(output_root),
                "--title",
                "装配式结构抗震性能研究",
                "--sections",
                "Introduction,Method,Results,Discussion",
                "--skip-section-draft",
            )

            self.assertTrue((output_root / "queries" / "query_plan.json").exists())
            self.assertTrue((output_root / "retrieval" / "retrieval_trace.jsonl").exists())
            self.assertTrue((output_root / "claims" / "claim_registry.jsonl").exists())
            state = json.loads((output_root / "workflow_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["query_plan_status"], "ready")
            self.assertEqual(state["retrieval_status"], "ready")
            self.assertEqual(state["claim_check_status"], "ready")

    def test_section_router_writes_versioned_draft_from_retrieval_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "out"
            output_root.mkdir()
            make_cards(output_root)
            (output_root / "workflow_state.json").write_text(
                json.dumps(
                    {
                        "carding_status": "ready",
                        "query_plan_status": "ready",
                        "retrieval_status": "ready",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            write_jsonl(
                output_root / "retrieval" / "retrieval_trace.jsonl",
                [
                    {
                        "query_id": "results_comparison_001",
                        "section": "Results",
                        "section_purpose": "comparison",
                        "query": "峰值承载力 对比",
                        "results": [
                            {
                                "card_id": "card_result_1",
                                "source_id": "core_001",
                                "content_kind": "result",
                                "evidence_preview": "试件 UJ-1 的峰值承载力高于 RC。",
                                "page_or_location": "12",
                            }
                        ],
                    }
                ],
            )

            run_script(
                "skills/section-writing-router/scripts/route_section_writing.py",
                "--output-root",
                str(output_root),
                "--section",
                "Results",
            )

            draft = output_root / "draft_sections" / "results_v1.md"
            self.assertTrue(draft.exists())
            text = draft.read_text(encoding="utf-8")
            self.assertIn("UJ-1", text)
            self.assertIn("[source_id:core_001; card_id:card_result_1]", text)
            state = json.loads((output_root / "workflow_state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["section_draft_status"], "drafted")


if __name__ == "__main__":
    unittest.main()
