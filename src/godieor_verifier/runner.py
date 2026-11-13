"""Local macOS runner. Fixed recipes; no user-supplied shell or product approval."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import time
import uuid

from .engine import digest, report, markdown, strict_json, EXIT_CODES, hexadecimal
from .subject import subject_digest
from .snapshot import snapshot, copy_build, freeze, git, migration_manifest

IMAGE = 'postgres:16-alpine@sha256:16bc17c64a573ef34162af9298258d1aec548232985b33ed7b1eac33ba35c229'


def now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def backend_test_files(root):
    """Match the backend's CJS and ESM test suites without implicit discovery."""
    root = Path(root)
    paths = sorted(p for pattern in ('*.test.cjs', '*.test.mjs')
                   for p in (root/'tests').glob(pattern))
    if not paths or any(p.is_symlink() or not p.is_file() for p in paths):
        raise ValueError('backend test files missing or not regular')
    return [str(p.relative_to(root)) for p in paths]


def profile(build, source, home, tools, cache):
    # Deliberately no access to the invoking user's HOME, repos, Docker socket or artifacts.
    # Foundation atomic writes / Xcode use the host's Darwin user temp directory
    # (/private/var/folders/.../T) even with TMPDIR redirected. Do not grant that
    # shared directory here: it is outside the per-run writable boundary.
    # A separately isolated build identity/environment is still required for iOS.
    quote = lambda p: json.dumps(str(p))
    def aliases(paths):
        result=[]
        for path in paths:
            resolved=str(Path(path).resolve());result.append(resolved)
            if resolved.startswith('/private/tmp/'):
                result.append(resolved.removeprefix('/private'))
        return result
    reads = [build, source, home, cache, *tools, '/System', '/usr', '/bin', '/sbin',
             '/Library', '/Applications/Xcode.app', '/opt/homebrew', '/dev',
             '/private/etc', '/private/var/db', '/private/var/run']
    return '\n'.join(['(version 1)', '(deny default)',
        '(allow process* sysctl-read mach-lookup ipc-posix* signal)', '(allow file-read-metadata)', '(allow file-read* (literal "/"))', '(allow file-map-executable)',
        '(allow file-read* ' + ' '.join('(subpath '+quote(p)+')' for p in aliases(reads)) + ')',
        '(allow file-write* '+ ' '.join('(subpath '+quote(p)+')' for p in aliases([build, home])) + ')',
        '(allow file-write* (literal "/dev/null"))',
        '(allow network-outbound (remote ip "localhost:*"))',
        '(allow network-inbound (local ip "localhost:*"))'])


def command(argv, cwd, env, log, timeout=300, policy=None):
    started = now()
    wrapped = ['/usr/bin/sandbox-exec', '-p', policy, *argv] if policy else argv
    with Path(log).open('wb') as stream:
        proc = subprocess.Popen(wrapped, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        timed_out = False
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(proc.pid, signal.SIGKILL)
            code = proc.wait()
        finally:
            # Clean this process group only. A setsid descendant can escape; full
            # lifecycle containment is deliberately not claimed or marked verified.
            try: os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
    return {'command': argv, 'exit_code': code, 'started_at': started,
            'finished_at': now(), 'timeout': timed_out, 'log': str(log),
            'log_sha256': digest(Path(log).read_bytes())}


@contextmanager
def database():
    name = 'godieor-vfy-' + uuid.uuid4().hex[:12]
    password = secrets.token_hex(24)
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'),
           'HOME': os.environ.get('HOME', ''), 'POSTGRES_PASSWORD': password}
    def docker(*args):
        return subprocess.check_output(['docker', *args], env=env, stderr=subprocess.PIPE,
                                       timeout=60).decode().strip()
    attempted = False
    try:
        attempted = True
        docker('run', '--pull=never', '--rm', '-d', '--name', name,
               '-e', 'POSTGRES_USER=godieor', '-e', 'POSTGRES_DB=godieor_vfy',
               '-e', 'POSTGRES_PASSWORD', '-p', '127.0.0.1::5432',
               '--tmpfs', '/var/lib/postgresql/data', IMAGE)
        ready = False
        for _ in range(60):
            try:
                docker('exec', name, 'pg_isready', '-U', 'godieor', '-d', 'godieor_vfy')
                ready = True; break
            except subprocess.CalledProcessError: time.sleep(.25)
        if not ready: raise RuntimeError('일회용 DB 준비 시간 초과')
        port = docker('port', name, '5432/tcp').rsplit(':', 1)[1]
        yield name, 'postgresql://godieor:'+password+'@127.0.0.1:'+port+'/godieor_vfy'
    finally:
        if attempted:
            try: docker('rm', '-f', name)
            except subprocess.CalledProcessError:
                # Missing container is benign only when inspect confirms absence.
                ids=docker('ps','-aq','--filter','name=^/'+name+'$')
                if ids: raise RuntimeError('DB 정리 실패')


def prepare(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    manifests = {}
    for key in ('app', 'backend'):
        repo = getattr(args, key)
        base, head = getattr(args, key+'_base'), getattr(args, key+'_head')
        if not hexadecimal(base,40): raise ValueError("base 고정SHA 형식 오류")
        # Verify base without executing checkout content.
        if git(repo, 'rev-parse', '--verify', base+'^{commit}').decode().strip() != base:
            raise ValueError('base commit 불일치')
        source = out/'source'/key
        manifests[key] = snapshot(repo, head, source)
        copy_build(source, out/'build'/key)
        freeze(source)
        manifests[key]['base_sha'] = base
        manifests[key]['dirty_excluded'] = bool(git(repo, 'status', '--porcelain'))
    backend = out/'source/backend'
    contract_bytes = (backend/'contracts/manifest.json').read_bytes()
    contract = strict_json(contract_bytes)
    for name, expected in contract['files'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('contract 경로 탈출')
        if digest((backend/'contracts'/path).read_bytes()) != expected:
            raise ValueError('contract manifest 내용 불일치')
    reference = strict_json((out/'source/app/docs/api/contract-reference.json').read_bytes())
    if reference['manifestSha256'] != digest(contract_bytes):
        raise ValueError('app/backend 계약 digest 불일치')
    migrations, migration_digest = migration_manifest(backend)
    write_json(out/'migration-manifest.json', migrations)
    acceptance_bytes = args.acceptance.read_bytes()
    acceptance = strict_json(acceptance_bytes)
    (out/'acceptance.json').write_bytes(acceptance_bytes)
    verifier_root = Path(__file__).resolve().parents[2]
    state = {p.relative_to(verifier_root).as_posix(): digest(p.read_bytes())
             for directory in ('src', 'scripts', 'schemas')
             for p in sorted((verifier_root/directory).rglob('*'))
             if p.is_file() and '__pycache__' not in p.parts}
    write_json(out/'verifier-state.json', state)
    e = {'schema_version': 2, 'run_id': out.name, 'started_at': now(), 'finished_at': now(),
         'app': {'base_sha': args.app_base, 'head_sha': args.app_head},
         'backend': {'base_sha': args.backend_base, 'head_sha': args.backend_head},
         'contract': {'version': contract['contractVersion'], 'sha256': digest(contract_bytes)},
         'migrations': {'sha256': migration_digest},
         'acceptance': {'version': acceptance['version'], 'sha256': digest(acceptance_bytes)},
         'verifier': {'sha': git(verifier_root,'rev-parse','HEAD').decode().strip(),
                      'dirty': bool(git(verifier_root,'status','--porcelain')),
                      'state_sha256': digest(json.dumps(state,sort_keys=True,separators=(',',':')).encode())},
         'execution': {'mode': 'external-runner', 'isolation_verified': False,
                       'tool_versions': {'runner': 'local-v1'}}, 'checks': []}
    e['review'] = {'status': 'PENDING', 'app_head_sha':args.app_head,
        'acceptance_sha256':digest(acceptance_bytes), 'subject_sha256':subject_digest(e),
        'run_id':e['run_id'], 'model':None,'settings':{},'started_at':None,'finished_at':None,'findings':[]}
    write_json(out/'snapshot-manifest.json',manifests)
    return out, e, acceptance


def api_check_evidence(item, check_id, evidence):
    """Bind one actual process result; success also requires its expected receipt."""
    status = 'ERROR' if item['timeout'] else ('PASS' if item['exit_code']==0 else 'FAIL')
    if status == 'PASS':
        try:
            raw=Path(item['log']).read_bytes().splitlines()[-1]
            receipt=strict_json(raw)
            if (set(receipt)!={'schema_version','suite','status','scope','assertions'} or
                type(receipt['schema_version']) is not int or receipt['schema_version']!=1 or
                receipt['suite']!=item['id'].removeprefix('api-') or
                receipt['status']!='PASS' or receipt['scope']!='backend-api-synthetic' or
                type(receipt['assertions']) is not int or receipt['assertions']<1):
                status='ERROR'
        except (ValueError, OSError, IndexError, TypeError, KeyError, RecursionError):
            status='ERROR'
    # The current filter policy and the old draft disagree on cross-category scope.
    # Preserve the observation but never promote a subset to full draft acceptance.
    if check_id=='filter-intersection' and status=='PASS': status='SKIPPED'
    return {'id':check_id,'run_id':evidence['run_id'],'app_head_sha':evidence['app']['head_sha'],
        'acceptance_sha256':evidence['acceptance']['sha256'],'subject_sha256':subject_digest(evidence),
        'status':status,'command':item['command'],'exit_code':item['exit_code'],
        'started_at':item['started_at'],'finished_at':item['finished_at'],'evidence':item['log'],
        'scope':'backend-api-synthetic',
        'coverage':'current policy observations; draft conflict unresolved' if check_id=='filter-intersection' else 'API component; iOS flow is separate'}


def secret_check_evidence(item, evidence):
    status='ERROR' if item['timeout'] or item['exit_code'] not in (0,1) else ('PASS' if item['exit_code']==0 else 'FAIL')
    if status=='PASS':
        try:
            receipt=strict_json(Path(item['log']).read_bytes().splitlines()[-1])
            from .secret_check import POLICY_VERSION
            if (set(receipt)!={'schema_version','policy','status','scope','files','findings','errors'} or
                type(receipt.get('schema_version')) is not int or receipt['schema_version']!=1 or
                type(receipt.get('findings')) is not int or type(receipt.get('errors')) is not int or
                receipt.get('policy')!=POLICY_VERSION or
                receipt.get('status')!='PASS' or receipt.get('scope')!='literal-credentials-and-labelled-pii' or
                type(receipt.get('files')) is not int or receipt['files']<1 or
                receipt.get('findings')!=0 or receipt.get('errors')!=0):status='ERROR'
        except (OSError,ValueError,TypeError,IndexError,AttributeError,RecursionError):status='ERROR'
    return {'id':'secret-check','run_id':evidence['run_id'],'app_head_sha':evidence['app']['head_sha'],
        'acceptance_sha256':evidence['acceptance']['sha256'],'subject_sha256':subject_digest(evidence),
        'status':status,'command':item['command'],'exit_code':item['exit_code'],
        'started_at':item['started_at'],'finished_at':item['finished_at'],'evidence':item['log'],
        'scope':'literal-credentials-and-labelled-pii',
        'coverage':'fixed app/backend source, fixtures, completed step logs, unsigned app bundle; literal policy only'}


def ios_build_command(build):
    """Verifier-owned unsigned recipe; no product shell script is launched."""
    return ['/usr/bin/xcodebuild', '-project', str(build/'ios/GODIEOR.xcodeproj'),
            '-scheme', 'GODIEOR', '-configuration', 'Debug', '-sdk', 'iphonesimulator',
            '-destination', 'generic/platform=iOS Simulator',
            '-derivedDataPath', str(build/'work/DerivedData'), 'CODE_SIGNING_ALLOWED=NO', 'build']


def run(args):
    out, evidence, acceptance = prepare(args)
    logs = out/'logs'; logs.mkdir()
    steps = []
    def save():
        evidence['finished_at'] = now()
        binding = subject_digest(evidence)
        ios = next((item for item in steps if item['id']=='ios-build'), None)
        if ios:
            evidence['checks'].append({'id':'ios-build','run_id':evidence['run_id'],
                'app_head_sha':args.app_head,'acceptance_sha256':evidence['acceptance']['sha256'],
                'subject_sha256':binding,'status':'ERROR' if ios['timeout'] else ('PASS' if ios['exit_code']==0 else 'FAIL'),
                'command':ios['command'],'exit_code':ios['exit_code'],
                'started_at':ios['started_at'],'finished_at':ios['finished_at'],'evidence':ios['log']})
        for suite, cid in [('event-identity','event-identity'),('time-semantics','time-semantics'),('api-filter-observations','filter-intersection')]:
            item=next((s for s in steps if s['id']=='api-'+suite),None)
            if item: evidence['checks'].append(api_check_evidence(item,cid,evidence))
        secret=next((s for s in steps if s['id']=='secret-check'),None)
        if secret:evidence['checks'].append(secret_check_evidence(secret,evidence))
        for cid in acceptance['required_checks']:
            if not any(c['id']==cid for c in evidence['checks']):
                evidence['checks'].append({'id':cid,'run_id':evidence['run_id'],
                    'app_head_sha':args.app_head,'acceptance_sha256':evidence['acceptance']['sha256'],
                    'subject_sha256':binding,'status':'SKIPPED'})
        write_json(out/'steps.json', steps)
        write_json(out/'evidence.json', evidence)
        result = report((out/'acceptance.json').read_bytes(),(out/'evidence.json').read_bytes(),2)
        write_json(out/'report.json',result)
        (out/'report.md').write_text(markdown(result))
        return EXIT_CODES[result['verdict']]
    try:
        if args.execute:
            home=out/'build/home';home.mkdir()
            tmp=home/'tmp';tmp.mkdir()
            (home/'npm-user.config').touch();(home/'npm-global.config').touch()
            node=args.node.resolve(); npm=args.npm_cli.resolve();cache=home/'npm-cache'
            shutil.copytree(args.npm_cache.resolve()/'_cacache', cache/'_cacache')
            trusted=out/'trusted';trusted.mkdir()
            shutil.copyfile(Path(__file__).with_name('database-smoke.cjs'),trusted/'database-smoke.cjs')
            shutil.copyfile(Path(__file__).with_name('api-checks.cjs'),trusted/'api-checks.cjs')
            env={'PATH':str(node.parent)+':/usr/bin:/bin:/usr/sbin:/sbin', 'HOME':str(home),
                 'TMPDIR':str(tmp), 'LANG':'en_US.UTF-8', 'CI':'1',
                 'CFFIXED_USER_HOME':str(home),'XDG_CACHE_HOME':str(home/'cache'),
                 'CLANG_MODULE_CACHE_PATH':str(home/'clang-cache'),
                 'COLLECTION_SCHEDULE_ENABLED':'false',
                 'DATABASE_URL':'postgresql://unconfigured@127.0.0.1:1/unconfigured'}
            def step(name, argv, key, timeout=300, extra=None, fetch=False, sandboxed=True):
                policy=profile(out/'build',out/'source',home,[node.parent,npm.parent.parent,trusted],cache)
                if fetch: policy+='\n(allow network-outbound)'
                if not sandboxed: policy=None
                item=command(argv,out/'build'/key,{**env,**(extra or {})},logs/(name+'.log'),timeout,policy)
                item['id']=name; item['execution_policy']='sandboxed' if sandboxed else 'local-reviewed'; steps.append(item)
                if item['exit_code'] or item['timeout']:raise RuntimeError('step 실패: '+name)
                return item
            version_step=step('node-version',[str(node),'--version'],'backend')
            evidence['execution']['tool_versions']['node']=(logs/'node-version.log').read_text().strip()
            # Probe generated canary boundaries, never read real secrets.
            canary=out/'private-canary';canary.write_text('synthetic-secret')
            probe = '\n'.join([
                'import pathlib',
                'def denied_read(path):',
                ' try: pathlib.Path(path).read_bytes()',
                ' except PermissionError: return',
                ' raise SystemExit(4)',
                'denied_read('+repr(str(canary))+')',
                'denied_read('+repr(str(args.app.resolve()/'AGENTS.md'))+')',
                'p=pathlib.Path('+repr(str(out/'source/app/AGENTS.md'))+')',
                'assert p.read_bytes()',
                'try: p.write_text("forbidden")',
                'except PermissionError: pass',
                'else: raise SystemExit(5)',
                'p=pathlib.Path('+repr(str(home/'probe'))+')',
                'p.write_text("ok");assert p.read_text()=="ok"'])
            step('boundary-probe',['/usr/bin/python3','-c',probe],'backend')
            evidence['execution']['tool_versions']['ios_execution_policy']='local-reviewed (same UID; no OS isolation)'
            # iOS compilation is independent of Docker/backend availability.
            try:
                step('ios-build',ios_build_command(out/'build/app'),'app',600,sandboxed=False)
            except RuntimeError:
                pass  # The actual failed step remains in evidence; backend checks continue.
            if node.name != 'node': raise ValueError('Node 실행 파일 필요')
            step('dependencies',[str(node),str(npm),'ci','--ignore-scripts',
                '--registry=https://registry.npmjs.org/','--userconfig='+str(home/'npm-user.config'),'--globalconfig='+str(home/'npm-global.config'),
                *(['--prefer-offline'] if args.fetch_dependencies else ['--offline']), '--cache',str(cache)],
                'backend',600,fetch=args.fetch_dependencies)
            step('generate',[str(node),'node_modules/prisma/build/index.js','generate'],'backend',fetch=args.fetch_dependencies)
            step('compile',[str(node),'node_modules/typescript/bin/tsc','-p','tsconfig.json'],'backend')
            tests=backend_test_files(out/'build/backend')
            step('backend-tests',[str(node),'--test',*tests],'backend')
            with database() as (name,url):
                write_json(out/'database.json',{'container':name,'image':IMAGE,'temporary':True})
                extra={'DATABASE_URL':url,'CURSOR_SIGNING_KEY':secrets.token_hex(32),'API_HOST':'127.0.0.1'}
                step('migration',[str(node),'node_modules/prisma/build/index.js','migrate','deploy'],'backend',extra=extra)
                for suite in ['event-identity','time-semantics','api-filter-observations']:
                    try:
                        step('api-'+suite,[str(node),str(trusted/'api-checks.cjs'),suite],'backend',extra=extra)
                    except RuntimeError:
                        pass  # Retain each actual failure and continue the other independent observations.
                step('database-smoke',[str(node),str(trusted/'database-smoke.cjs')],'backend',extra=extra)

    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        # Do not print secrets, subprocess argv/environment or Docker error text.
        write_json(out/'runner-error.json',{'type':type(exc).__name__, 'message':'실행 단계 오류; steps/log 확인'})
    if args.execute:
        try:
            scanner_env={'PATH':'/usr/bin:/bin','PYTHONPATH':str(Path(__file__).resolve().parents[1]),'LANG':'en_US.UTF-8'}
            # Keep this redacted scanner log outside the input logs directory.
            item=command([sys.executable,'-m','godieor_verifier.secret_check','--run',str(out)],
                         out,scanner_env,out/'secret-check.log',120,None)
            item.update(id='secret-check',execution_policy='verifier-scanner')
            steps.append(item)
        except (OSError,subprocess.SubprocessError):
            write_json(out/'scanner-error.json',{'message':'scanner execution failed; no success inferred'})
    return save()


def main():
    parser=argparse.ArgumentParser(description='고정 snapshot 및 macOS 로컬 실행 (미승인 검사 SKIPPED)')
    for key in ('app','backend'):
        parser.add_argument('--'+key,type=Path,required=True)
        for suffix in ('base','head'):parser.add_argument('--'+key+'-'+suffix,required=True)
    parser.add_argument('--acceptance',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--fetch-dependencies',action='store_true',help='npm ci(ignore-scripts)·Prisma 생성 준비 단계만 외부망 허용')
    parser.add_argument('--node',type=Path)
    parser.add_argument('--npm-cli',type=Path)
    parser.add_argument('--npm-cache',type=Path)
    args=parser.parse_args()
    if args.execute and not all((args.node,args.npm_cli,args.npm_cache)):
        parser.error('--execute에는 node/npm-cli/npm-cache 필요')
    try:return run(args)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print('ERROR: snapshot 준비 실패 ('+type(exc).__name__+')')
        return 3


if __name__=='__main__':raise SystemExit(main())
