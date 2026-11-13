import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest
from godieor_verifier.snapshot import snapshot, freeze, copy_build, migration_manifest
from godieor_verifier.runner import command, profile, backend_test_files


class RunnerTests(unittest.TestCase):
    def test_esm_failure_is_executed_even_when_commonjs_passes(self):
        node = shutil.which('node')
        if not node:
            self.skipTest('Node is unavailable')
        tests = self.root/'tests';tests.mkdir()
        (tests/'pass.test.cjs').write_text("require('node:test')('synthetic CJS pass',()=>{});\n")
        (tests/'fail.test.mjs').write_text("throw new Error('synthetic ESM failure');\n")
        (tests/'fixture.mjs').write_text("throw new Error('not a test');\n")
        result = subprocess.run([node, '--test', *backend_test_files(self.root)],
                                cwd=self.root, capture_output=True, text=True,
                                env={'PATH':'/usr/bin:/bin'}, timeout=20)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('synthetic ESM failure', result.stdout + result.stderr)
        self.assertNotIn('not a test', result.stdout + result.stderr)

    def test_no_suite_or_linked_suite_is_an_error(self):
        with self.assertRaises(ValueError):backend_test_files(self.root)
        tests=self.root/'tests';tests.mkdir()
        target=self.root/'synthetic';target.write_text('not executed')
        (tests/'linked.test.mjs').symlink_to(target)
        with self.assertRaises(ValueError):backend_test_files(self.root)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root/'repo'; self.repo.mkdir()
        self.git('init','-q');self.git('config','user.name','synthetic');self.git('config','user.email','synthetic@example.invalid')

    def tearDown(self):
        for p in self.root.rglob('*'):
            if not p.is_symlink():p.chmod(p.stat().st_mode | 0o700)
        self.tmp.cleanup()

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git('add','.');self.git('commit','-qm','synthetic')
        return self.git('rev-parse','HEAD')

    def test_pinned_snapshot_excludes_dirty_and_untracked(self):
        (self.repo/'a').write_text('committed'); sha=self.commit()
        (self.repo/'a').write_text('dirty');(self.repo/'untracked').write_text('not included')
        source=self.root/'source';manifest=snapshot(self.repo,sha,source)
        self.assertEqual((source/'a').read_text(),'committed')
        self.assertFalse((source/'untracked').exists())
        freeze(source);copy_build(source,self.root/'build')
        (self.root/'build/a').write_text('compiled')
        self.assertEqual((source/'a').read_text(),'committed')
        self.assertEqual(manifest['sha'],sha)

    def test_symlink_is_rejected(self):
        (self.repo/'a').symlink_to('/etc/passwd');sha=self.commit()
        with self.assertRaises(ValueError):snapshot(self.repo,sha,self.root/'source')

    def test_lfs_pointer_rejected(self):
        (self.repo/'a').write_text('version https://git-lfs.github.com/spec/v1\noid sha256:fake')
        with self.assertRaises(ValueError):snapshot(self.repo,self.commit(),self.root/'source')

    def test_sha_must_be_full_commit(self):
        with self.assertRaises(ValueError):snapshot(self.repo,'HEAD',self.root/'source')

    def test_migration_changes_and_renames_change_digest(self):
        root=self.repo/'prisma/migrations';root.mkdir(parents=True)
        (root/'a.sql').write_text('CREATE TABLE x();')
        _,a=migration_manifest(self.repo)
        (root/'a.sql').rename(root/'b.sql');_,b=migration_manifest(self.repo)
        self.assertNotEqual(a,b)
        (root/'b.sql').write_text('DROP TABLE x;');_,c=migration_manifest(self.repo)
        self.assertNotEqual(b,c)

    def test_command_collects_exit_and_digest(self):
        item=command(['/usr/bin/false'],self.root,{'PATH':'/usr/bin:/bin'},self.root/'log',2)
        self.assertNotEqual(item['exit_code'],0)
        self.assertEqual(len(item['log_sha256']),64)
        self.assertFalse(item['timeout'])

    def test_command_timeout(self):
        item=command(['/bin/sleep','5'],self.root,{},self.root/'log',.01)
        self.assertTrue(item['timeout'])
        self.assertNotEqual(item['exit_code'],0)

    def test_profile_does_not_allow_default_access(self):
        p=profile(self.root/'b',self.root/'s',self.root/'h',[],self.root/'c')
        self.assertIn('(deny default)',p)
        self.assertNotIn('(allow default)',p)
        self.assertNotIn('/var/run/docker.sock',p)
        # Foundation/Xcode atomic output needs host Darwin temp, but exposing it
        # would let checked code modify unrelated user-scoped temporary files.
        writable=next(line for line in p.splitlines()
                      if line.startswith('(allow file-write* (subpath '))
        self.assertEqual(writable, '(allow file-write* '
                         f'(subpath "{(self.root/"b").resolve()}") '
                         f'(subpath "{(self.root/"h").resolve()}"))')

    def test_replace_ref_cannot_change_pinned_blob(self):
        (self.repo/'a').write_text('original');original=self.commit()
        (self.repo/'a').write_text('replacement');replacement=self.commit()
        self.git('replace',original,replacement)
        snapshot(self.repo,original,self.root/'source')
        self.assertEqual((self.root/'source/a').read_text(),'original')

    def test_local_export_attributes_do_not_change_snapshot(self):
        (self.repo/'a').write_text('pinned');sha=self.commit()
        (self.repo/'.git/info/attributes').write_text('a export-ignore\n')
        snapshot(self.repo,sha,self.root/'source')
        self.assertEqual((self.root/'source/a').read_text(),'pinned')

    def test_fsmonitor_program_is_not_executed(self):
        from godieor_verifier.snapshot import git
        marker=self.root/'marker';hook=self.root/'monitor'
        hook.write_text('#!/bin/sh\ntouch '+str(marker)+'\n');hook.chmod(0o755)
        self.git('config','core.fsmonitor',str(hook))
        git(self.repo,'status','--porcelain')
        self.assertFalse(marker.exists())

    def test_case_collisions_are_rejected(self):
        for name,content in [('A',b'upper'),('a',b'lower')]:
            oid=subprocess.check_output(['git','-C',str(self.repo),'hash-object','-w','--stdin'],input=content).decode().strip()
            self.git('update-index','--add','--cacheinfo','100644',oid,name)
        self.git('commit','-qm','case collision');sha=self.git('rev-parse','HEAD')
        with self.assertRaises(ValueError):snapshot(self.repo,sha,self.root/'source')

    def test_database_creation_timeout_attempts_cleanup(self):
        from unittest.mock import patch
        from godieor_verifier.runner import database
        calls=[]
        def docker(argv,**kwargs):
            calls.append(argv[1])
            if argv[1]=='run':raise subprocess.TimeoutExpired(argv,60)
            return b''
        with patch('godieor_verifier.runner.subprocess.check_output',side_effect=docker):
            with self.assertRaises(subprocess.TimeoutExpired):
                with database():pass
        self.assertEqual(calls,['run','rm'])

    def test_promisor_missing_object_does_not_execute_remote_helper(self):
        (self.repo/'a').write_text('payload');sha=self.commit()
        oid=self.git('rev-parse',sha+':a')
        (self.repo/'.git/objects'/oid[:2]/oid[2:]).unlink()
        marker=self.root/'remote-marker';helper=self.root/'remote-helper'
        helper.write_text('#!/bin/sh\ntouch '+str(marker)+'\n');helper.chmod(0o755)
        self.git('config','remote.origin.promisor','true')
        self.git('config','remote.origin.partialclonefilter','blob:none')
        self.git('config','remote.origin.url','ext::'+str(helper))
        self.git('config','protocol.ext.allow','always')
        with self.assertRaises(subprocess.CalledProcessError):snapshot(self.repo,sha,self.root/'source')
        self.assertFalse(marker.exists())
