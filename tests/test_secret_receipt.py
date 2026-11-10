import json
from pathlib import Path
import tempfile
import unittest
from godieor_verifier.runner import secret_check_evidence
from godieor_verifier.secret_check import POLICY_VERSION

ROOT=Path(__file__).resolve().parents[1]

class SecretReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.log=Path(self.tmp.name)/'scan.log'
        self.e=json.loads((ROOT/'examples/evidence-v2.json').read_text())
        self.item=dict(command=['synthetic'],exit_code=0,timeout=False,log=str(self.log),
            started_at='2026-11-10T00:00:00Z',finished_at='2026-11-10T00:00:00Z')
        self.receipt=dict(schema_version=1,policy=POLICY_VERSION,status='PASS',
            scope='literal-credentials-and-labelled-pii',files=5,findings=0,errors=0)
    def tearDown(self):self.tmp.cleanup()
    def evaluate(self):
        self.log.write_text(json.dumps(self.receipt)+'\n')
        return secret_check_evidence(self.item,self.e)['status']
    def test_clean_receipt_pass_and_scanner_failure(self):
        self.assertEqual(self.evaluate(),'PASS')
        self.item['exit_code']=1;self.assertEqual(self.evaluate(),'FAIL')
        self.item['exit_code']=3;self.assertEqual(self.evaluate(),'ERROR')
    def test_strict_numeric_fields(self):
        for key,value in [('schema_version',True),('findings',False),('errors',0.0),('files',True)]:
            original=dict(self.receipt);self.receipt[key]=value
            self.assertEqual(self.evaluate(),'ERROR');self.receipt=original
    def test_empty_malformed_or_deep_receipt_is_error(self):
        for raw in [b'',b'invalid',b'['*2000+b'0'+b']'*2000]:
            self.log.write_bytes(raw)
            self.assertEqual(secret_check_evidence(self.item,self.e)['status'],'ERROR')
