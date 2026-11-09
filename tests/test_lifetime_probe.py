import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from godieor_verifier.lifetime_probe import run


class LifetimeProbeTests(unittest.TestCase):
    def test_real_timeout_observes_bounded_detached_work(self):
        with tempfile.TemporaryDirectory() as root:
            result = run(Path(root) / 'out', 'timeout')
        self.assertTrue(result['step']['timeout'])
        self.assertEqual(result['status'], 'escape_observed')
        self.assertFalse(result['post_return_progress']['ordinary'])
        self.assertTrue(result['post_return_progress']['detached'])
        self.assertNotEqual(result['parent']['pgid'], result['detached']['pgid'])
        self.assertTrue(result['self_expired']['detached'])
        self.assertFalse(result['isolation_verified'])
        self.assertFalse(result['cleanup_verified'])

    def test_failure_before_worker_ready_is_inconclusive(self):
        with tempfile.TemporaryDirectory() as root:
            with patch('godieor_verifier.lifetime_probe.command', return_value={
                    'timeout': False, 'exit_code': 71}), patch('godieor_verifier.lifetime_probe.time.sleep'):
                result = run(Path(root) / 'out', 'normal', sandbox=True)
            self.assertEqual(result['status'], 'inconclusive')
            self.assertNotIn('post_return_progress', result)
            self.assertTrue((Path(root) / 'out/result.json').is_file())

    def test_existing_output_is_not_reused(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / 'out'
            out.symlink_to(Path(root) / 'missing')
            with self.assertRaises(FileExistsError):
                run(out, 'normal')
            self.assertTrue(out.is_symlink())
