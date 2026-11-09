"""Bounded synthetic reproduction of process-group cleanup limits (P5)."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time

from .runner import command, profile, write_json
from .engine import digest

NAMES = ('ordinary', 'detached')


def heartbeats(out):
    values = {}
    for name in NAMES:
        try:
            values[name] = int((out / (name + '.heartbeat')).read_text())
        except (OSError, ValueError):
            values[name] = None
    return values


def run(output, mode, sandbox=False):
    output.mkdir(mode=0o700)
    out = output.resolve()
    worker = Path(__file__).resolve().parents[2] / 'scripts/lifetime-worker.py'
    shutil.copyfile(worker, out / 'worker.py')
    home = out / 'home'
    home.mkdir(mode=0o700)
    (home / 'tmp').mkdir(mode=0o700)
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(home), 'TMPDIR': str(home / 'tmp')}
    policy = profile(out, out, home, [Path(sys.executable).resolve().parent], home) if sandbox else None
    result = {'mode': mode, 'sandbox': sandbox, 'effective_uid': os.geteuid(),
              'worker_sha256': digest(worker.read_bytes()), 'isolation_verified': False,
              'status': 'environment_error'}
    if policy:
        (out / 'sandbox.sb').write_text(policy)
        result['profile_sha256'] = digest(policy.encode())
    try:
        result['step'] = command([sys.executable, str(out / 'worker.py'), str(out), mode],
                                 out, env, out / 'worker.log', timeout=.9, policy=policy)
        # A changing counter proves actual post-return work, unlike kill(pid, 0),
        # which also reports zombies and may observe a reused PID.
        first = heartbeats(out)
        time.sleep(.2)
        second = heartbeats(out)
        result['samples'] = [first, second]
        ready = (out / 'parent.ready').is_file()
        expected_exit = (result['step']['timeout'] if mode == 'timeout' else
                         not result['step']['timeout'] and result['step']['exit_code'] == 0)
        result['status'] = 'inconclusive'
        if ready and expected_exit and all(first[n] is not None and second[n] is not None for n in NAMES):
            progressed = {name: second[name] > first[name] for name in NAMES}
            result['post_return_progress'] = progressed
            result['status'] = 'escape_observed' if progressed['detached'] else 'escape_not_observed'
        for name in (*NAMES, 'parent'):
            path = out / (name + '.ready')
            if path.exists():
                result[name] = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        result['error'] = str(exc)
    finally:
        # No PID-targeted cleanup: synthetic workers self-expire within 4s.
        # Waiting is a diagnostic courtesy, not containment of arbitrary code.
        time.sleep(4.2)
        result['self_expired'] = {name: (out / (name + '.done')).exists() for name in NAMES}
        result['cleanup_verified'] = False
        write_json(out / 'result.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('normal', 'timeout'), required=True)
    parser.add_argument('--sandbox', action='store_true')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        result = run(args.output, args.mode, args.sandbox)
    except OSError as exc:
        parser.exit(64, str(exc) + '\n')
    print(json.dumps(result, indent=2))
    # Reproduced escape is a failed lifecycle boundary, never diagnostic PASS.
    return 2 if result['status'] in ('escape_observed', 'escape_not_observed') else 3


if __name__ == '__main__':
    raise SystemExit(main())
