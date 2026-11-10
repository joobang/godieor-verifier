import argparse
import json
import os
from pathlib import Path
import pwd
import tempfile
import unittest
from unittest.mock import patch

from godieor_verifier.dedicated_ios import (
    dedicated_identity, require_denied, run, single_run, verify_input,
)
from godieor_verifier.engine import digest


class DedicatedIOSTests(unittest.TestCase):
    def test_readable_and_nonexistent_paths_are_not_permission_denials(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'remains readable'):
                require_denied(Path(temp))
            with self.assertRaisesRegex(ValueError, 'inconclusive'):
                require_denied(Path(temp) / 'missing')

    def test_wrong_caller_home_cannot_authorize_a_temp_grant(self):
        with self.assertRaisesRegex(ValueError, 'does not match'):
            dedicated_identity(os.getuid(), Path('/nonexistent-account-home'), Path('/missing'))

    def test_same_uid_fails_closed_before_any_execution(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(pwd.getpwuid(os.getuid()).pw_dir)
            args = argparse.Namespace(out=Path(temp) / 'out', caller_uid=os.getuid(),
                                      caller_home=home, original_app=home / 'README.md')
            with patch('godieor_verifier.dedicated_ios.command') as execute:
                result = run(args)
            execute.assert_not_called()
            self.assertEqual(result['status'], 'blocked')
            self.assertEqual(result['ios_build'], 'not_executed')
            self.assertFalse(result['isolation_verified'])

    def test_run_lock_excludes_concurrency_and_releases_after_exception(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            with self.assertRaisesRegex(RuntimeError, 'synthetic failure'):
                with single_run(home):
                    with self.assertRaises(BlockingIOError):
                        with single_run(home):
                            self.fail('concurrent run admitted')
                    raise RuntimeError('synthetic failure')
            with single_run(home):
                pass

    def test_lock_symlink_is_rejected_without_modifying_target(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            target = home / 'keep'
            target.write_text('keep')
            (home / '.godieor-ios-probe.lock').symlink_to(target)
            with self.assertRaises(OSError):
                with single_run(home):
                    self.fail('symlink lock accepted')
            self.assertEqual(target.read_text(), 'keep')

    def test_input_digest_extra_files_and_symlinks_are_checked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            app = root / 'app'
            app.mkdir()
            (app / 'a').write_text('pinned')
            files = {'a': digest(b'pinned')}
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'sha': 'a' * 40, 'files': files,
                'tree_sha256': digest(json.dumps(files, sort_keys=True,
                    separators=(',', ':'), ensure_ascii=False).encode())}))
            # Tests run as input owner; only the build-UID access query is mocked.
            with patch('godieor_verifier.dedicated_ios.os.access', return_value=False):
                verify_input(app, manifest, os.getuid())
                (app / 'a').write_text('changed')
                with self.assertRaisesRegex(ValueError, 'content mismatch'):
                    verify_input(app, manifest, os.getuid())
                (app / 'a').write_text('pinned')
                (app / 'extra').write_text('extra')
                with self.assertRaisesRegex(ValueError, 'content mismatch'):
                    verify_input(app, manifest, os.getuid())
                (app / 'extra').unlink()
                (app / 'link').symlink_to(app / 'a')
                with self.assertRaisesRegex(ValueError, 'without links'):
                    verify_input(app, manifest, os.getuid())
            with self.assertRaisesRegex(ValueError, 'read-only'):
                verify_input(app, manifest, os.getuid())

    def test_compile_failure_never_runs_product_build(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            account = root / 'account'
            account.mkdir()
            app = root / 'app'
            app.mkdir()
            darwin = root / 'T'
            darwin.mkdir()
            args = argparse.Namespace(out=root / 'out', app=app, manifest=root / 'manifest',
                                      caller_uid=123, caller_home=root / 'caller',
                                      original_app=root / 'caller/README.md')
            with patch('godieor_verifier.dedicated_ios.dedicated_identity',
                       return_value=(account, darwin, {'isolation_verified': False})), \
                 patch('godieor_verifier.dedicated_ios.verify_input', return_value={'sha': 'a'*40}), \
                 patch('godieor_verifier.dedicated_ios.command', side_effect=[
                     {'exit_code': 0, 'timeout': False}, {'exit_code': 1, 'timeout': False}]) as execute:
                result = run(args)
            self.assertEqual(execute.call_count, 2)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['ios_build'], 'not_executed')
            self.assertEqual([s['id'] for s in result['steps']], ['xcode-version', 'foundation-compile'])
