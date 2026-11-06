import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from godieor_verifier.engine import assess, digest, report


ROOT = Path(__file__).resolve().parents[1]


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.raw = (ROOT / "requirements/acceptance.yaml").read_bytes()
        self.acceptance = json.loads(self.raw)
        self.evidence = json.loads((ROOT / "examples/evidence.json").read_text())
        # Synthetic approval exists only in memory to exercise the PASS branch.
        # It is not user approval and is never written to requirements/.
        self.acceptance.update(status="approved", approved_by="SYNTHETIC-TEST-ONLY",
                               approved_at="2026-11-06T06:00:00Z", approval_record="synthetic://test")
        self.evidence["execution"].update(mode="external-runner", isolation_verified=True)

    def evaluate(self):
        raw = json.dumps(self.acceptance).encode()
        sha = digest(raw)
        self.evidence["acceptance"]["sha256"] = sha
        self.evidence["review"]["acceptance_sha256"] = sha
        for check in self.evidence["checks"]:
            check["acceptance_sha256"] = sha
        return assess(self.acceptance, self.evidence, sha)["verdict"]

    def test_complete_synthetic_evidence_exercises_pass(self):
        self.assertEqual(self.evaluate(), "PASS")

    def test_deliberate_check_failure(self):
        self.evidence["checks"][0].update(status="FAIL", exit_code=1)
        self.assertEqual(self.evaluate(), "FAIL")

    def test_pass_label_cannot_hide_nonzero_exit(self):
        self.evidence["checks"][0]["exit_code"] = 1
        self.assertEqual(self.evaluate(), "FAIL")

    def test_missing_required_check(self):
        self.evidence["checks"].pop()
        self.assertEqual(self.evaluate(), "ERROR")

    def test_environment_error(self):
        self.evidence["checks"][0].update(status="ERROR", exit_code=None)
        self.assertEqual(self.evaluate(), "ERROR")

    def test_skipped_check_is_not_success(self):
        self.evidence["checks"][0]["status"] = "SKIPPED"
        self.assertEqual(self.evaluate(), "ERROR")

    def test_draft_cannot_pass(self):
        self.acceptance["status"] = "draft"
        self.assertEqual(self.evaluate(), "REVIEW_REQUIRED")

    def test_missing_approval_receipt_is_error(self):
        self.acceptance["approval_record"] = None
        self.assertEqual(self.evaluate(), "ERROR")

    def test_stale_sha_review_cannot_apply_to_new_head(self):
        self.evidence["app"]["head_sha"] = "4" * 40
        self.assertEqual(self.evaluate(), "ERROR")

    def test_new_review_cannot_reuse_old_check_results(self):
        self.evidence["app"]["head_sha"] = "4" * 40
        self.evidence["review"]["app_head_sha"] = "4" * 40
        self.assertEqual(self.evaluate(), "ERROR")

    def test_check_run_binding(self):
        self.evidence["checks"][0]["run_id"] = "older-run"
        self.assertEqual(self.evaluate(), "ERROR")

    def test_missing_check_sha_binding(self):
        del self.evidence["checks"][0]["app_head_sha"]
        self.assertEqual(self.evaluate(), "ERROR")

    def test_stale_check_acceptance_binding(self):
        self.evidence["checks"][0]["acceptance_sha256"] = "f" * 64
        self.assertEqual(assess(json.loads(self.raw), self.evidence, digest(self.raw))["verdict"], "ERROR")

    def test_review_schema_rejects_extra_fields_and_array_settings(self):
        for mutation in ({"unexpected": True}, {"settings": {"temperature": []}}):
            with self.subTest(mutation=mutation):
                original = copy.deepcopy(self.evidence["review"])
                self.evidence["review"].update(mutation)
                self.assertEqual(self.evaluate(), "ERROR")
                self.evidence["review"] = original

    def test_pending_review_still_requires_schema_fields(self):
        self.evidence["review"]["status"] = "PENDING"
        del self.evidence["review"]["findings"]
        self.assertEqual(self.evaluate(), "ERROR")

    def test_malformed_check_does_not_hide_later_failure(self):
        del self.evidence["checks"][0]["command"]
        self.evidence["checks"][1].update(status="FAIL", exit_code=1)
        self.assertEqual(self.evaluate(), "ERROR")
        sha = self.evidence["acceptance"]["sha256"]
        result = assess(self.acceptance, self.evidence, sha)
        self.assertTrue(result["errors"])
        self.assertTrue(result["failures"])

    def test_invalid_json_unicode_and_depth_produce_cli_error_report(self):
        for raw in (b"[" * 1100 + b"]" * 1100,
                    b'{"run_id":"\\ud800"}'):
            with self.subTest(raw_length=len(raw)), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "input.json"
                path.write_bytes(raw)
                run = subprocess.run([str(ROOT / "scripts/verifier"), "--acceptance",
                    str(ROOT / "requirements/acceptance.yaml"), "--evidence", str(path),
                    "--out", str(Path(tmp) / "out")], capture_output=True, text=True)
                self.assertEqual(run.returncode, 3, run.stderr)
                result = json.loads((Path(tmp) / "out/report.json").read_text())
                self.assertEqual(result["verdict"], "ERROR")

    def test_duplicate_json_keys_and_nonfinite_numbers_are_error(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            self.assertEqual(report(self.raw, raw)["verdict"], "ERROR")

    def test_changed_acceptance_file_digest_is_error(self):
        self.assertEqual(assess(self.acceptance, self.evidence, "f" * 64)["verdict"], "ERROR")

    def test_ai_prose_does_not_replace_checks(self):
        self.evidence["checks"] = []
        self.evidence["review"]["settings"] = {"summary": "all tests passed"}
        self.assertEqual(self.evaluate(), "ERROR")

    def test_even_critical_ai_finding_needs_confirmation(self):
        self.evidence["review"]["findings"] = [{"id": "F-1", "requirement_id": "GD-007",
            "severity": "critical", "evidence": "fixture/path:1", "reproduction": "repro steps",
            "uncertainty": "not executed; hypothesis"}]
        self.assertEqual(self.evaluate(), "REVIEW_REQUIRED")

    def test_review_error_blocks_pass(self):
        self.evidence["review"]["status"] = "ERROR"
        self.assertEqual(self.evaluate(), "ERROR")

    def test_pending_review_blocks_pass(self):
        self.evidence["review"]["status"] = "PENDING"
        self.assertEqual(self.evaluate(), "REVIEW_REQUIRED")

    def test_unverified_isolation_blocks_pass(self):
        self.evidence["execution"]["isolation_verified"] = False
        self.assertEqual(self.evaluate(), "REVIEW_REQUIRED")

    def test_fixture_cannot_be_product_pass(self):
        self.evidence["execution"]["mode"] = "fixture"
        self.assertEqual(self.evaluate(), "REVIEW_REQUIRED")

    def test_empty_acceptance_checks_are_error(self):
        self.acceptance["required_checks"] = []
        self.assertEqual(self.evaluate(), "ERROR")

    def test_duplicate_check_is_error(self):
        self.evidence["checks"].append(copy.deepcopy(self.evidence["checks"][0]))
        self.assertEqual(self.evaluate(), "ERROR")

    def test_missing_log_is_error(self):
        del self.evidence["checks"][0]["evidence"]
        self.assertEqual(self.evaluate(), "ERROR")

    def test_boolean_exit_code_is_not_integer(self):
        self.evidence["checks"][0]["exit_code"] = False
        self.assertEqual(self.evaluate(), "ERROR")

    def test_timezone_required(self):
        self.evidence["started_at"] = "2026-11-06T06:00:00"
        self.assertEqual(self.evaluate(), "ERROR")

    def test_malformed_json_generates_error_report(self):
        result = report(self.raw, b"{broken")
        self.assertEqual(result["verdict"], "ERROR")

    def test_structurally_wrong_json_generates_error(self):
        self.assertEqual(report(self.raw, b"[]")["verdict"], "ERROR")

    def test_demo_cli_exit_and_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = subprocess.run([str(ROOT / "scripts/verifier"), "--acceptance",
                str(ROOT / "requirements/acceptance.yaml"), "--evidence",
                str(ROOT / "examples/evidence.json"), "--out", tmp], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2, run.stderr)
            output = json.loads((Path(tmp) / "report.json").read_text())
            self.assertEqual(output["verdict"], "REVIEW_REQUIRED")
            self.assertIn("REVIEW_REQUIRED", (Path(tmp) / "report.md").read_text())


if __name__ == "__main__":
    unittest.main()
