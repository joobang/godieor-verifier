from pathlib import Path
import subprocess
import unittest
from godieor_verifier.runner import ios_build_command

ROOT=Path(__file__).resolve().parents[1]


class LocalVerificationTests(unittest.TestCase):
    def test_ios_recipe_unsigned_fixed_and_no_product_script(self):
        argv=ios_build_command(Path('/tmp/pinned-app'))
        self.assertEqual(argv[0],'/usr/bin/xcodebuild')
        self.assertIn('CODE_SIGNING_ALLOWED=NO',argv)
        self.assertIn('generic/platform=iOS Simulator',argv)
        self.assertNotIn('/bin/sh',argv)
        self.assertEqual(argv[argv.index('-derivedDataPath')+1],'/tmp/pinned-app/work/DerivedData')

    def test_retired_wrappers_do_not_request_account_credentials(self):
        for name in ('probe-dedicated-ios','check-isolated-ios-host'):
            result=subprocess.run([str(ROOT/'scripts'/name)],capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,2)
            self.assertIn('폐기',result.stderr)

    def test_independent_ios_failure_and_docker_failure_are_preserved(self):
        import copy
        import json
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import patch
        from contextlib import contextmanager
        from godieor_verifier.runner import run
        from godieor_verifier.engine import digest
        for ios_exit, db_fails in [(65,False),(0,True)]:
            with self.subTest(ios_exit=ios_exit, db_fails=db_fails), tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp);(out/'build').mkdir();(out/'cache/_cacache').mkdir(parents=True)
                suites=out/'build/backend/tests';suites.mkdir(parents=True)
                (suites/'synthetic.test.cjs').write_text('// synthetic CJS suite\n')
                (suites/'synthetic.test.mjs').write_text('// synthetic ESM suite\n')
                raw=(ROOT/'requirements/acceptance.yaml').read_bytes();(out/'acceptance.json').write_bytes(raw)
                acceptance=json.loads(raw)
                evidence=json.loads((ROOT/'examples/evidence-v2.json').read_text())
                evidence['checks']=[]; evidence['review']['status']='PENDING'
                evidence['execution']['mode']='external-runner'
                args=SimpleNamespace(execute=True,node=out/'tools/node',npm_cli=out/'tools/npm-cli.js',
                    npm_cache=out/'cache',app=out/'original-app',app_head=evidence['app']['head_sha'],fetch_dependencies=False)
                def command(argv,cwd,env,log,timeout,policy):
                    Path(log).write_text('v24.19.0\n' if Path(log).stem=='node-version' else 'synthetic')
                    code=ios_exit if Path(log).stem=='ios-build' else 0
                    return dict(command=argv,exit_code=code,started_at='2026-11-10T00:00:00Z',
                        finished_at='2026-11-10T00:00:00Z',timeout=False,log=str(log),log_sha256=digest(Path(log).read_bytes()))
                @contextmanager
                def database():
                    if db_fails: raise OSError('synthetic Docker unavailable')
                    yield 'synthetic','postgresql://synthetic@localhost:1/synthetic'
                with patch('godieor_verifier.runner.prepare',return_value=(out,evidence,acceptance)), \
                     patch('godieor_verifier.runner.command',side_effect=command), \
                     patch('godieor_verifier.runner.database',database):
                    self.assertEqual(run(args),3)
                e=json.loads((out/'evidence.json').read_text())
                ios=next(c for c in e['checks'] if c['id']=='ios-build')
                self.assertEqual(ios['status'],'FAIL' if ios_exit else 'PASS')
                steps=json.loads((out/'steps.json').read_text())
                self.assertTrue(any(s['id']=='backend-tests' for s in steps))
                backend=next(s for s in steps if s['id']=='backend-tests')
                self.assertIn('tests/synthetic.test.cjs',backend['command'])
                self.assertIn('tests/synthetic.test.mjs',backend['command'])
                self.assertEqual(any(s['id']=='database-smoke' for s in steps),not db_fails)
