"""Read-only preflight for a proposed dedicated macOS build identity.

It deliberately never switches users, creates accounts, or certifies isolation.
"""
import argparse
import json
import os
from pathlib import Path
import pwd
import subprocess


def assess(caller_uid, effective_uid, home, darwin_temp, caller_home):
    """Return explicit failed prerequisites without writing probe files."""
    failures = []
    if effective_uid == 0:
        failures.append('root_is_not_a_build_identity')
    if effective_uid == caller_uid:
        failures.append('same_uid_as_caller')
    home_path = Path(home).resolve()
    caller_path = Path(caller_home).resolve()
    if home_path == caller_path or home_path.is_relative_to(caller_path):
        failures.append('home_overlaps_caller_home')
    temp_path = Path(darwin_temp).resolve() if darwin_temp else None
    if temp_path is None or not temp_path.is_dir():
        failures.append('darwin_temp_missing')
    else:
        stat = temp_path.stat()
        if stat.st_uid != effective_uid:
            failures.append('darwin_temp_owner_mismatch')
        if stat.st_mode & 0o077:
            failures.append('darwin_temp_has_group_or_other_access')
    return {'ready_for_manual_probe': not failures, 'failures': failures,
            'effective_uid': effective_uid,
            'darwin_temp_physical': str(temp_path) if temp_path else None,
            'isolation_verified': False}


def main():
    p = argparse.ArgumentParser(description='전용 macOS 빌드 UID 읽기 전용 사전점검')
    p.add_argument('--caller-uid', type=int, required=True,
                   help='기존 개발 계정의 UID (서로 달라야 함)')
    p.add_argument('--caller-home', type=Path, required=True,
                   help='기존 개발 계정의 HOME (빌드 계정에서 겹치지 않아야 함)')
    args = p.parse_args()
    try:
        temp = subprocess.check_output(['/usr/bin/getconf', 'DARWIN_USER_TEMP_DIR'],
                                       timeout=10, stderr=subprocess.DEVNULL).decode().strip()
    except (OSError, subprocess.SubprocessError):
        temp = ''
    result = assess(args.caller_uid, os.geteuid(), pwd.getpwuid(os.geteuid()).pw_dir,
                    temp, args.caller_home)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ready_for_manual_probe'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
