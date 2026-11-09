"""Extract pinned Git commits without links, submodules, traversal or LFS pointers."""
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import os
import unicodedata
from .engine import digest, hexadecimal


def git(repo, *args):
    env = {'PATH':'/usr/bin:/bin:/usr/sbin:/sbin', 'HOME':'/var/empty',
           'GIT_CONFIG_NOSYSTEM':'1', 'GIT_CONFIG_GLOBAL':'/dev/null',
           'GIT_NO_REPLACE_OBJECTS':'1', 'GIT_OPTIONAL_LOCKS':'0',
           'GIT_NO_LAZY_FETCH':'1', 'GIT_ALLOW_PROTOCOL':''}
    return subprocess.check_output(['/usr/bin/git', '--no-replace-objects',
        '-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null',
        '-C',str(repo),*args], env=env, stderr=subprocess.PIPE, timeout=60)


def snapshot(repo, sha, destination):
    if not hexadecimal(sha, 40):
        raise ValueError('40자리 고정 commit SHA 필요')
    if git(repo, 'rev-parse', '--verify', sha + '^{commit}').decode().strip() != sha:
        raise ValueError('commit SHA 불일치')
    entries = []
    canonical = {}
    for entry in git(repo, 'ls-tree', '-r', '-z', sha).split(b'\0'):
        if not entry: continue
        metadata, rawpath = entry.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        path = PurePosixPath(rawpath.decode('utf-8'))
        if mode not in ('100644','100755') or kind != 'blob':
            raise ValueError('symlink/submodule/특수 Git entry 거부')
        if path.is_absolute() or '..' in path.parts or not path.parts or '.git' in path.parts:
            raise ValueError('snapshot 경로 오류')
        for i in range(1,len(path.parts)+1):
            prefix=PurePosixPath(*path.parts[:i]).as_posix()
            key=unicodedata.normalize('NFD',prefix).casefold()
            if key in canonical and canonical[key] != prefix:
                raise ValueError('파일시스템 대소문자/Unicode 경로 충돌')
            canonical[key]=prefix
        entries.append((path,mode,oid))
    destination=Path(destination); destination.mkdir(parents=True,exist_ok=False)
    files={}
    # Read raw blobs: Git replace refs, export-ignore/export-subst and local
    # info/attributes must never change the pinned commit's contents.
    for path, mode, oid in entries:
        data=git(repo,'cat-file','blob',oid)
        if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
            raise ValueError('미해결 LFS pointer 거부')
        target=destination.joinpath(*path.parts); target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(data)
        target.chmod(0o755 if mode=='100755' else 0o644)
        files[path.as_posix()]=digest(data)
    return {'sha':sha, 'tree_sha256':digest(json.dumps(files,sort_keys=True,
            separators=(',',':'),ensure_ascii=False).encode()), 'files':files}


def freeze(directory):
    for p in sorted(Path(directory).rglob('*'), reverse=True):
        p.chmod(0o555 if p.is_dir() or p.stat().st_mode & 0o111 else 0o444)
    Path(directory).chmod(0o555)


def copy_build(source, destination):
    shutil.copytree(source, destination)
    for p in Path(destination).rglob('*'):
        p.chmod(p.stat().st_mode | 0o200)


def migration_manifest(backend):
    root = Path(backend) / 'prisma/migrations'
    if not root.is_dir():
        raise ValueError('migration 디렉터리 누락')
    files = {p.relative_to(root).as_posix(): digest(p.read_bytes())
             for p in sorted(root.rglob('*')) if p.is_file()}
    raw = json.dumps(files, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
    return files, digest(raw)
