import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from godieor_verifier.isolated_host import assess


class IsolatedHostTests(unittest.TestCase):
    def test_same_user_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            result = assess(501, 501, temp, temp, temp)
        self.assertIn('same_uid_as_caller', result['failures'])
        self.assertIn('home_overlaps_caller_home', result['failures'])
        self.assertFalse(result['isolation_verified'])

    def test_dedicated_user_directory_only_passes_preflight(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            with patch('godieor_verifier.isolated_host.Path.stat') as mock_stat:
                mock_stat.return_value.st_uid = 502
                mock_stat.return_value.st_mode = 0o40700
                result = assess(501, 502, '/Users/dedicated-build', path,
                                '/Users/developer')
        self.assertTrue(result['ready_for_manual_probe'])
        self.assertFalse(result['isolation_verified'])

    def test_root_and_shared_temp_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            with patch('godieor_verifier.isolated_host.Path.stat') as mock_stat:
                mock_stat.return_value.st_uid = 501
                mock_stat.return_value.st_mode = 0o40777
                result = assess(501, 0, '/var/root', path, '/Users/developer')
        self.assertIn('root_is_not_a_build_identity', result['failures'])
        self.assertIn('darwin_temp_owner_mismatch', result['failures'])
        self.assertIn('darwin_temp_has_group_or_other_access', result['failures'])

    def test_missing_darwin_temp_is_rejected(self):
        result = assess(501, 502, '/Users/builder', '', '/Users/developer')
        self.assertIn('darwin_temp_missing', result['failures'])
