import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from godieor_verifier.secret_check import scan_roots, matches


class SecretCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
    def tearDown(self):self.tmp.cleanup()

    def test_literal_tokens_and_private_key(self):
        for value in ['ghp_'+'A'*36,'AKIA'+'A'*16,'sk-proj-'+'a'*30,
                      'GOCSPX-'+'b'*24,'-----BEGIN PRIVATE KEY-----']:
            with self.subTest(value=value[:5]):self.assertTrue(matches(value.encode()))

    def test_missing_root_is_error(self):
        self.assertEqual(scan_roots({'bundle':self.root/'missing'})['status'],'ERROR')

    def test_secret_values_never_written_to_result(self):
        token='ghp_'+'A'*36;(self.root/'key.txt').write_text(token)
        result=scan_roots({'source':self.root})
        self.assertEqual(result['status'],'FAIL');self.assertNotIn(token,json.dumps(result))

    def test_binary_and_utf16_and_binary_plist(self):
        token='GOCSPX-'+'x'*25
        (self.root/'blob').write_bytes(b'\x00\xff'+token.encode()+b'\x00')
        (self.root/'utf16.txt').write_bytes(token.encode('utf-16'))
        (self.root/'Info.plist').write_bytes(plistlib.dumps({'client_secret':token},fmt=plistlib.FMT_BINARY))
        result=scan_roots({'bundle':self.root});self.assertEqual(result['status'],'FAIL')
        self.assertEqual({f['path_id'] for f in result['findings']},{__import__('hashlib').sha256(p.encode()).hexdigest() for p in ['blob','utf16.txt','Info.plist']})

    def test_templates_and_reserved_email(self):
        for value in ['DATABASE_URL=postgresql://dev:replace-with-local-random-value@127.0.0.1/db',
                      'CURSOR_SIGNING_KEY=replace-with-at-least-32-random-bytes',
                      'email="someone@example.test"','email="someone@example.com"']:
            self.assertEqual(matches(value.encode()),[])
        self.assertTrue(matches(b'api_key="replace-with-a-real-secret-value"'))
        self.assertTrue(matches(b'email="person@private-domain.co.kr"'))

    def test_symlink_is_error_not_external_read(self):
        (self.root/'outside').symlink_to('/etc/passwd')
        self.assertEqual(scan_roots({'source':self.root})['status'],'ERROR')

    def test_clean_file_inventory(self):
        (self.root/'safe').write_text('no credential here')
        result=scan_roots({'source':self.root});self.assertEqual(result['status'],'PASS')
        self.assertEqual(len(result['files'][0]['sha256']),64)

    def test_template_interpolation_not_literal_secret(self):
        self.assertEqual(matches(b'postgresql://user:${password}@localhost/db'),[])
        self.assertTrue(matches(b'postgresql://user:password@localhost/db'))

    def test_exemptions_do_not_apply_to_changed_or_other_files(self):
        (self.root/'bad.js').write_text('https://user:password@cjnews.cj.net/story/')
        self.assertEqual(scan_roots({'backend-source':self.root})['status'],'FAIL')
        path=self.root/'tests/reviewed-publish.test.cjs';path.parent.mkdir();path.write_text('https://user:password@cjnews.cj.net/story/')
        self.assertEqual(scan_roots({'backend-source':self.root})['status'],'FAIL')

    def test_empty_required_root_is_error(self):
        self.assertEqual(scan_roots({'bundle':self.root})['status'],'ERROR')

    def test_unreadable_child_directory_is_error(self):
        (self.root/'safe').write_text('safe')
        blocked=self.root/'blocked';blocked.mkdir();(blocked/'secret').write_text('ghp_'+'A'*36)
        blocked.chmod(0)
        try:self.assertEqual(scan_roots({'source':self.root})['status'],'ERROR')
        finally:blocked.chmod(0o700)

    def test_plist_preserves_generic_labels(self):
        for fmt in [plistlib.FMT_XML,plistlib.FMT_BINARY]:
            (self.root/'Info.plist').write_bytes(plistlib.dumps({'api_key':'genericSecretValue123456',
                'email':'private@real-domain.co.kr','phone':'+82 10 1234 5678'},fmt=fmt))
            result=scan_roots({'bundle':self.root});self.assertEqual(result['status'],'FAIL')
            self.assertTrue({'credential-assignment','labelled-email','labelled-phone'} <= {f['rule'] for f in result['findings']})

    def test_secret_in_filename_is_not_disclosed(self):
        token='ghp_'+'B'*36;(self.root/token).write_text(token)
        result=scan_roots({'source':self.root});self.assertEqual(result['status'],'FAIL')
        self.assertNotIn(token,json.dumps(result));self.assertIn('path_id',result['findings'][0])

    def test_linked_parent_of_root_is_error(self):
        (self.root/'actual/sub').mkdir(parents=True);(self.root/'actual/sub/safe').write_text('safe')
        (self.root/'linked').symlink_to(self.root/'actual',target_is_directory=True)
        self.assertEqual(scan_roots({'source':self.root/'linked/sub'})['status'],'ERROR')
