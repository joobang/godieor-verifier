import copy
import json
from pathlib import Path
import unittest
import subprocess
import tempfile
from godieor_verifier.engine import assess, digest, report
from godieor_verifier.subject import subject_digest

ROOT = Path(__file__).resolve().parents[1]


class SubjectV2Tests(unittest.TestCase):
    def setUp(self):
        self.a = json.loads((ROOT / 'requirements/acceptance.yaml').read_text())
        self.e = json.loads((ROOT / 'examples/evidence-v2.json').read_text())
        # Approval and external execution claims below are synthetic in-memory only.
        self.a.update(status='approved', approved_by='SYNTHETIC-TEST-ONLY',
                      approved_at='2026-11-06T06:00:00Z', approval_record='synthetic://test')
        self.sha = digest(json.dumps(self.a).encode())
        self.e['acceptance']['sha256'] = self.sha
        self.e['execution'].update(mode='external-runner', isolation_verified=True)
        for c in self.e['checks']: c['acceptance_sha256'] = self.sha
        self.e['review']['acceptance_sha256'] = self.sha
        self.bind()

    def bind(self):
        binding = subject_digest(self.e)
        for c in self.e['checks']: c['subject_sha256'] = binding
        self.e['review']['subject_sha256'] = binding

    def verdict(self):
        return assess(self.a, self.e, self.sha)['verdict']

    def test_synthetic_complete(self):
        self.assertEqual(self.verdict(), 'PASS')

    def test_each_changed_subject_rejects_old_checks_and_review(self):
        original = copy.deepcopy(self.e)
        for key, field, value in [('app','head_sha','a'*40),('backend','head_sha','b'*40),
                                  ('backend','base_sha','c'*40),('contract','version','other'),
                                  ('contract','sha256','d'*64),('migrations','sha256','e'*64),
                                  ('verifier','state_sha256','f'*64),('verifier','sha','a'*40)]:
            with self.subTest(key=key, field=field):
                self.e = copy.deepcopy(original); self.e[key][field] = value
                self.assertEqual(self.verdict(), 'ERROR')

    def test_new_checks_cannot_reuse_old_review(self):
        self.e['backend']['head_sha'] = 'a'*40
        for c in self.e['checks']: c['subject_sha256'] = subject_digest(self.e)
        self.assertEqual(self.verdict(), 'ERROR')

    def test_new_review_cannot_reuse_old_checks(self):
        self.e['migrations']['sha256'] = 'a'*64
        self.e['review']['subject_sha256'] = subject_digest(self.e)
        self.assertEqual(self.verdict(), 'ERROR')

    def test_review_run_binding(self):
        self.e['review']['run_id'] = 'other-run'
        self.assertEqual(self.verdict(), 'ERROR')

    def test_missing_and_malformed_subject(self):
        original = copy.deepcopy(self.e)
        for key in ('backend', 'contract', 'migrations'):
            self.e = copy.deepcopy(original); del self.e[key]
            self.assertEqual(self.verdict(), 'ERROR')
        self.e = copy.deepcopy(original); self.e['backend']['head_sha'] = 'short'; self.bind()
        self.assertEqual(self.verdict(), 'ERROR')

    def test_v2_downgrade_rejected(self):
        self.e['schema_version'] = 1
        self.assertEqual(self.verdict(), 'ERROR')

    def test_missing_binding_rejected(self):
        del self.e['checks'][0]['subject_sha256']
        self.assertEqual(self.verdict(), 'ERROR')

    def test_missing_check_failure_environment_error(self):
        original = copy.deepcopy(self.e)
        for state, expected in [('FAIL', 'FAIL'), ('ERROR','ERROR'), ('SKIPPED','ERROR')]:
            self.e = copy.deepcopy(original); self.e['checks'][0]['status'] = state
            self.assertEqual(self.verdict(), expected)
        self.e = copy.deepcopy(original); self.e['checks'].pop()
        self.assertEqual(self.verdict(), 'ERROR')

    def test_draft_and_fixture_are_not_product_pass(self):
        raw = (ROOT / 'requirements/acceptance.yaml').read_bytes()
        e = (ROOT / 'examples/evidence-v2.json').read_bytes()
        result = report(raw, e)
        self.assertEqual(result['verdict'], 'REVIEW_REQUIRED')
        self.assertEqual(result['evidence_schema_version'], 2)

    def test_canonical_key_order_is_stable(self):
        other = json.loads(json.dumps(self.e, sort_keys=True))
        self.assertEqual(subject_digest(other), subject_digest(self.e))

    def test_unexpected_subject_field_rejected(self):
        self.e['backend']['branch'] = 'dev'; self.bind()
        self.assertEqual(self.verdict(), 'ERROR')

    def test_stripped_v2_cannot_satisfy_required_v2(self):
        self.e['schema_version'] = 1
        for key in ('backend', 'contract', 'migrations'): del self.e[key]
        for check in self.e['checks']: del check['subject_sha256']
        del self.e['review']['subject_sha256']; del self.e['review']['run_id']
        self.assertEqual(assess(self.a, self.e, self.sha, 2)['verdict'], 'ERROR')
        self.assertEqual(assess(self.a, self.e, self.sha, 1)['verdict'], 'PASS')

    def test_invalid_binding_does_not_hide_later_failure(self):
        del self.e['checks'][0]['subject_sha256']
        self.e['checks'][1].update(status='FAIL', exit_code=1)
        result = assess(self.a, self.e, self.sha, 2)
        self.assertEqual(result['verdict'], 'ERROR')
        self.assertTrue(result['failures'])

    def test_cli_required_v2_rejects_v1(self):
        with tempfile.TemporaryDirectory() as out:
            result = subprocess.run([str(ROOT / 'scripts/verifier'), '--acceptance',
                str(ROOT / 'requirements/acceptance.yaml'), '--evidence',
                str(ROOT / 'examples/evidence.json'), '--out', out,
                '--require-schema-version', '2'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 3)
            result = json.loads((Path(out) / 'report.json').read_text())
            self.assertEqual(result['required_schema_version'], 2)
            self.assertEqual(result['evidence_schema_version'], 1)
