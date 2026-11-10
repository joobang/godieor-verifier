"""Opt-in diagnostics for a dedicated UID, never a product approval runner."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import pwd
import shutil
import stat
import subprocess

from .engine import digest, hexadecimal
from .foundation_probe import inspect_output
from .isolated_host import assess
from .runner import command, profile, write_json
from .snapshot import copy_build


def require_denied(path):
    """Require an actual permission denial, not a nonexistent test path."""
    try:
        fd = os.open(path, os.O_RDONLY)
    except PermissionError:
        return
    except OSError as exc:
        raise ValueError('access probe inconclusive: ' + str(path)) from exc
    else:
        os.close(fd)
        raise ValueError('caller path remains readable: ' + str(path))


def dedicated_identity(caller_uid, caller_home, original_app):
    uid = os.geteuid()
    caller = Path(pwd.getpwuid(caller_uid).pw_dir).resolve()
    if caller_uid <= 0 or caller != caller_home.resolve():
        raise ValueError('caller UID/HOME does not match OS account')
    original = original_app.absolute()
    if '..' in original.parts or not original.is_relative_to(caller):
        raise ValueError('original app probe must be inside caller HOME')
    temp = Path(subprocess.check_output(['/usr/bin/getconf', 'DARWIN_USER_TEMP_DIR'],
                                       timeout=10).decode().strip()).resolve()
    if not str(temp).startswith('/private/var/folders/') or temp.name != 'T':
        raise ValueError('unexpected physical Darwin temp location')
    home = Path(pwd.getpwuid(uid).pw_dir).resolve()
    result = assess(caller_uid, uid, home, temp, caller)
    if not result['ready_for_manual_probe']:
        raise ValueError('dedicated identity prerequisites: ' + ','.join(result['failures']))
    require_denied(caller)
    require_denied(original)
    return home, temp, result


@contextmanager
def single_run(home):
    # Advisory coordination for this diagnostic only. It does not contain
    # arbitrary same-UID code or prove escaped descendants were terminated.
    fd = os.open(home / '.godieor-ios-probe.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if info.st_uid != os.geteuid() or not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077:
            raise ValueError('unsafe dedicated run lock')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)


def verify_input(source, manifest_path, owner):
    info = manifest_path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != owner or
            info.st_mode & 0o022 or os.access(manifest_path, os.W_OK)):
        raise ValueError('manifest must be caller-owned and read-only to build UID')
    manifest = json.loads(manifest_path.read_text())
    if (not isinstance(manifest, dict) or not hexadecimal(manifest.get('sha'), 40) or
            not isinstance(manifest.get('files'), dict)):
        raise ValueError('invalid pinned app manifest')
    if source.is_symlink() or not source.is_dir():
        raise ValueError('app input must be a real directory')
    actual = {}
    for path in [source, *source.rglob('*')]:
        info = path.lstat()
        if (not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)) or
                info.st_uid != owner or info.st_mode & 0o022 or os.access(path, os.W_OK)):
            raise ValueError('app input must be caller-owned, read-only to build UID, without links')
        if path.is_file():
            actual[path.relative_to(source).as_posix()] = digest(path.read_bytes())
    canonical = json.dumps(actual, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    if actual != manifest['files'] or digest(canonical) != manifest.get('tree_sha256'):
        raise ValueError('pinned app snapshot content mismatch')
    return {'sha': manifest['sha'], 'tree_sha256': digest(canonical),
            'manifest_sha256': digest(manifest_path.read_bytes())}


def dedicated_policy(build, source, home, temp):
    # temp is obtained from getconf and checked by dedicated_identity, not CLI.
    paths = [str(temp)]
    if str(temp).startswith('/private/var/'):
        paths.append(str(temp).removeprefix('/private'))
    return profile(build, source, home, [], home) + '\n(allow file-read* file-write* ' + ' '.join(
        '(subpath ' + json.dumps(p) + ')' for p in paths) + ')'


def run(args):
    args.out.mkdir(mode=0o700)
    out = args.out.resolve()
    result = {'status': 'blocked', 'effective_uid': os.geteuid(),
              'isolation_verified': False, 'cleanup_verified': False, 'steps': []}
    try:
        account_home, temp, result['preflight'] = dedicated_identity(
            args.caller_uid, args.caller_home, args.original_app)
        result['caller_paths_denied'] = True
        source = args.app.absolute()
        result['app'] = verify_input(source, args.manifest, args.caller_uid)
        with single_run(account_home):
            build = out / 'build'
            build.mkdir()
            home = build / 'home'
            home.mkdir(mode=0o700)
            (home / 'tmp').mkdir(mode=0o700)
            copy_build(source, build / 'app')
            # Frozen staging has a non-writable root too; build scripts need to
            # create work/ directly under this private, build-owned copy.
            (build / 'app').chmod((build / 'app').stat().st_mode | 0o200)
            src = Path(__file__).resolve().parents[2] / 'scripts/foundation-atomic-probe.m'
            shutil.copyfile(src, build / 'foundation.m')
            result['foundation_source_sha256'] = digest(src.read_bytes())
            policy = dedicated_policy(build, source, home, temp)
            (out / 'sandbox.sb').write_text(policy)
            result['profile_sha256'] = digest(policy.encode())
            result['allowed_darwin_temp'] = str(temp)
            env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': str(home),
                   'TMPDIR': str(home / 'tmp'), 'CFFIXED_USER_HOME': str(home),
                   'CLANG_MODULE_CACHE_PATH': str(home / 'clang-cache'), 'LANG': 'en_US.UTF-8'}
            def step(name, argv, cwd, timeout):
                item = command(argv, cwd, env, out / (name + '.log'), timeout, policy)
                item['id'] = name
                result['steps'].append(item)
                write_json(out / 'result.json', result)
                if item['exit_code'] or item['timeout']:
                    raise ValueError('step failed: ' + name)
                return item
            step('xcode-version', ['/usr/bin/xcodebuild', '-version'], build, 30)
            step('foundation-compile', ['/usr/bin/clang', '-fobjc-arc', '-framework', 'Foundation',
                                       str(build / 'foundation.m'), '-o', str(build / 'probe')], build, 60)
            probe = step('foundation-write', [str(build / 'probe'), str(build)], build, 30)
            result['foundation_status'] = inspect_output(build, probe)
            if result['foundation_status'] != 'writes_verified':
                raise ValueError('Foundation plist content check failed')
            step('ios-build', ['/bin/sh', str(build / 'app/scripts/build-ios.sh')], build / 'app', 300)
            result['status'] = 'ios_build_succeeded'
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result['error'] = str(exc)
        if result['steps']:
            result['status'] = 'failed'
    finally:
        if not any(item['id'] == 'ios-build' for item in result['steps']):
            result['ios_build'] = 'not_executed'
        write_json(out / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--caller-uid', type=int, required=True)
    parser.add_argument('--caller-home', type=Path, required=True)
    parser.add_argument('--original-app', type=Path, required=True, help='existing app file inside caller HOME')
    parser.add_argument('--app', type=Path, required=True, help='read-only pinned snapshot')
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args)
    except OSError as exc:
        parser.exit(64, str(exc) + '\n')
    print(json.dumps(result, indent=2))
    # A successful diagnostic is not a product or isolation approval.
    return 0 if result['status'] == 'ios_build_succeeded' else 2


if __name__ == '__main__':
    raise SystemExit(main())
