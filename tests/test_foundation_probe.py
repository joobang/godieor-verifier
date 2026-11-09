import json
import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from godieor_verifier.foundation_probe import inspect_output, run


class FoundationProbeTests(unittest.TestCase):
    def test_success_requires_actual_plist_contents(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            step = {'exit_code': 0, 'timeout': False}
            self.assertEqual(inspect_output(out, step), 'invalid_output')
            for name in ('plain.plist', 'atomic.plist'):
                (out / name).write_bytes(plistlib.dumps({'probe': 'synthetic', 'version': 1}))
            self.assertEqual(inspect_output(out, step), 'writes_verified')
            (out / 'atomic.plist').write_bytes(plistlib.dumps({'probe': 'wrong'}))
            self.assertEqual(inspect_output(out, step), 'invalid_output')

    def test_failed_or_timed_out_execution_cannot_succeed(self):
        for code, timeout in ((71, False), (2, False), (0, True)):
            self.assertEqual(inspect_output(Path('/unused'),
                             {'exit_code': code, 'timeout': timeout}), 'execution_failed')

    def test_existing_output_and_dangling_symlink_are_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'existing'
            path.mkdir()
            marker = path / 'keep'
            marker.write_text('unchanged')
            with self.assertRaises(FileExistsError):
                run(path)
            link = Path(root) / 'link'
            link.symlink_to(Path(root) / 'missing')
            with self.assertRaises(FileExistsError):
                run(link)
            self.assertEqual(marker.read_text(), 'unchanged')
            self.assertTrue(link.is_symlink())

    def test_compile_failure_does_not_execute_probe(self):
        with tempfile.TemporaryDirectory() as root:
            with patch('godieor_verifier.foundation_probe.command',
                       return_value={'exit_code': 1, 'timeout': False}) as execute:
                result = run(Path(root) / 'out', sandbox=True)
            self.assertEqual(execute.call_count, 1)
            self.assertEqual(result['status'], 'compile_failed')
            self.assertFalse(result['isolation_verified'])
            self.assertTrue((Path(root) / 'out/result.json').is_file())

    def test_sandbox_failure_is_recorded_without_widening_policy(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / 'out'
            with patch('godieor_verifier.foundation_probe.command', side_effect=[
                    {'exit_code': 0, 'timeout': False},
                    {'exit_code': 71, 'timeout': False}]):
                result = run(out, sandbox=True)
            self.assertEqual(result['status'], 'execution_failed')
            self.assertEqual(result['steps'][-1]['exit_code'], 71)
            self.assertNotIn('(subpath ' + json.dumps(str(Path(root).resolve().parent)) + ')',
                             (out / 'sandbox.sb').read_text())
            self.assertFalse(result['isolation_verified'])
