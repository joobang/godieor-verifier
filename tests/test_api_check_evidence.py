import json
from pathlib import Path
import tempfile
import unittest
from godieor_verifier.runner import api_check_evidence

ROOT=Path(__file__).resolve().parents[1]


class ApiCheckEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.log=Path(self.tmp.name)/'api.log'
        self.e=json.loads((ROOT/'examples/evidence-v2.json').read_text())
        self.item=dict(id='api-event-identity',exit_code=0,timeout=False,command=['synthetic'],
            log=str(self.log),started_at='2026-11-10T00:00:00Z',finished_at='2026-11-10T00:00:00Z')
        self.receipt=dict(schema_version=1,suite='event-identity',status='PASS',scope='backend-api-synthetic',assertions=5)

    def tearDown(self):self.tmp.cleanup()

    def assess(self,cid='event-identity'):
        self.log.write_text(json.dumps(self.receipt)+'\n')
        return api_check_evidence(self.item,cid,self.e)

    def test_receipt_and_binding(self):
        result=self.assess();self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['run_id'],self.e['run_id']);self.assertEqual(len(result['subject_sha256']),64)

    def test_failure_and_timeout_not_hidden(self):
        self.item['exit_code']=1;self.assertEqual(self.assess()['status'],'FAIL')
        self.item['timeout']=True;self.assertEqual(self.assess()['status'],'ERROR')

    def test_zero_exit_without_receipt_is_error(self):
        self.log.write_text('not a receipt\n')
        self.assertEqual(api_check_evidence(self.item,'event-identity',self.e)['status'],'ERROR')

    def test_wrong_suite_empty_assertions_and_wrong_scope(self):
        for field,value in [('suite','other'),('assertions',0),('assertions',True),('scope','ios')]:
            with self.subTest(field=field):
                original=dict(self.receipt);self.receipt[field]=value
                self.assertEqual(self.assess()['status'],'ERROR');self.receipt=original

    def test_partial_filter_is_not_full_pass(self):
        self.item['id']='api-api-filter-observations';self.receipt['suite']='api-filter-observations'
        self.assertEqual(self.assess('filter-intersection')['status'],'SKIPPED')
        self.item['exit_code']=1
        self.assertEqual(self.assess('filter-intersection')['status'],'FAIL')

    def test_excessively_nested_receipt_is_error_not_crash(self):
        self.log.write_bytes(b'['*2000+b'0'+b']'*2000+b'\n')
        self.assertEqual(api_check_evidence(self.item,'event-identity',self.e)['status'],'ERROR')
