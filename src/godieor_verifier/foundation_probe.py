"""Synthetic Foundation diagnostics; never certifies host isolation."""
import argparse
import json
import os
from pathlib import Path
import plistlib

from .runner import command, profile, write_json
from .engine import digest


def inspect_output(out, step):
    if step['timeout'] or step['exit_code']:
        return 'execution_failed'
    expected = {'probe': 'synthetic', 'version': 1}
    try:
        for name in ('plain.plist', 'atomic.plist'):
            if plistlib.loads((out / name).read_bytes()) != expected:
                return 'invalid_output'
    except (OSError, ValueError, plistlib.InvalidFileException):
        return 'invalid_output'
    return 'writes_verified'


def run(output, sandbox=False):
    # mkdir is the exclusive reservation, including dangling symlink collisions.
    output.mkdir(mode=0o700)
    out = output.resolve()
    home = out / 'home'
    home.mkdir(mode=0o700)
    (home / 'tmp').mkdir(mode=0o700)
    source = Path(__file__).resolve().parents[2] / 'scripts/foundation-atomic-probe.m'
    env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'HOME': str(home),
           'TMPDIR': str(home / 'tmp'), 'CFFIXED_USER_HOME': str(home),
           'LANG': 'en_US.UTF-8'}
    result = {'mode': 'runner-sandbox' if sandbox else 'unrestricted',
              'effective_uid': os.geteuid(), 'isolation_verified': False,
              'source_sha256': digest(source.read_bytes()), 'steps': []}
    try:
        compile_step = command(['/usr/bin/clang', '-fobjc-arc', '-framework',
                                'Foundation', str(source), '-o', str(out / 'probe')],
                               out, env, out / 'compile.log', timeout=60)
        result['steps'].append(compile_step)
        result['status'] = 'compile_failed'
        if not compile_step['exit_code'] and not compile_step['timeout']:
            policy = None
            if sandbox:
                # No host Darwin T grant; use the same boundary as the runner.
                policy = profile(out, out, home, [], home)
                (out / 'sandbox.sb').write_text(policy)
                result['profile_sha256'] = digest(policy.encode())
            step = command([str(out / 'probe'), str(out)], out, env,
                           out / 'probe.log', timeout=30, policy=policy)
            result['steps'].append(step)
            result['status'] = inspect_output(out, step)
            # Observations are diagnostic only; successful exit and plist readback
            # are still required before reporting writes_verified.
            try:
                observation = json.loads((out / 'probe.log').read_text())
                if isinstance(observation, dict):
                    result['probe_observation'] = observation
            except (OSError, ValueError):
                pass
    except OSError as exc:
        result['status'] = 'environment_error'
        result['error'] = str(exc)
    write_json(out / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sandbox', action='store_true',
                        help='execute the compiled probe using the runner profile')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        result = run(args.output, args.sandbox)
    except OSError as exc:
        parser.exit(64, str(exc) + '\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'writes_verified' else 2


if __name__ == '__main__':
    raise SystemExit(main())
