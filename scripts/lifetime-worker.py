#!/usr/bin/env python3
"""Fixed synthetic process tree. No user commands; every descendant expires."""
import json
import os
from pathlib import Path
import signal
import sys
import time


def child(out, name, detached):
    # Even if the supervising diagnostic crashes, this worker stops by itself.
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(4)
    if detached:
        os.setsid()
    (out / (name + '.ready')).write_text(json.dumps(
        {'pid': os.getpid(), 'pgid': os.getpgrp(), 'sid': os.getsid(0)}))
    end = time.monotonic() + 2
    count = 0
    while time.monotonic() < end:
        count += 1
        pending = out / (name + '.pending')
        pending.write_text(str(count))
        pending.replace(out / (name + '.heartbeat'))
        time.sleep(.025)
    (out / (name + '.done')).write_text('self-expired')
    os._exit(0)


def main():
    out = Path(sys.argv[1])
    mode = sys.argv[2]
    signal.alarm(5)
    for name, detached in (('ordinary', False), ('detached', True)):
        if os.fork() == 0:
            child(out, name, detached)
    deadline = time.monotonic() + .5
    while not all((out / (name + '.ready')).exists() for name in ('ordinary', 'detached')):
        if time.monotonic() > deadline:
            return 3
        time.sleep(.005)
    (out / 'parent.ready').write_text(json.dumps({'pid': os.getpid(), 'pgid': os.getpgrp()}))
    if mode == 'timeout':
        time.sleep(4)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
