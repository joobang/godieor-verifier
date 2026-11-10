"""Literal credential and explicitly labelled PII scan; never emit matched values."""
import argparse
import json
import os
from pathlib import Path
import plistlib
import re
import sys

from .engine import digest

POLICY_VERSION = 'literal-secrets-1'
MAX_BYTES = 64 * 1024 * 1024
RULES = {
    'private-key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----',
    'aws-access-id': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'github-token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{40,255})\b',
    'openai-token': rb'\bsk-(?:proj-|svcacct-)[A-Za-z0-9_-]{20,255}',
    'google-client-secret': rb'\bGOCSPX-[A-Za-z0-9_-]{20,255}',
    'stripe-live-key': rb'\bsk_live_[A-Za-z0-9]{16,255}',
    'jwt': rb'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',
    'credential-assignment': rb'''(?i)["']?(?:api[_-]?key|client[_-]?secret|access[_-]?token|refresh[_-]?token|password|cursor_signing_key)["']?\s*[:=]\s*["']?([A-Za-z0-9_./+%:=@-]{16,255})''',
    'credential-url': rb'(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|https?)://[^\s:/@]+:([^\s/@]+)@',
    'korean-id-candidate': rb'(?<![0-9A-Za-z])[0-9]{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])-?[1-8][0-9]{6}(?![0-9A-Za-z])',
    'labelled-email': rb'''(?i)["']?email["']?\s*[:=]\s*["']([^\s"']+@[^\s"']+)''',
    'labelled-phone': rb'''(?i)["']?(?:phone|phone_number|telephone)["']?\s*[:=]\s*["'](\+?[0-9 ()-]{8,20})["']''',
}
# Exact public template values, not an arbitrary 'starts-with placeholder' bypass.
TEMPLATES = {b'replace-with-local-random-value', b'replace-with-at-least-32-random-bytes'}


# Reviewed negative URL fixture; pin the whole file to prevent broad exemptions.
NEGATIVE_URL_FIXTURE_SHA256 = '4714a010dc797bb5b34a36e3e2f08a3d4739ee7dede671c38ca3a74fdda8ebd4'


def matches(data, exemptions=()):
    found=[]
    for rule, pattern in RULES.items():
        for match in re.finditer(pattern, data):
            value=match.group(1) if match.lastindex else match.group(0)
            if value in TEMPLATES: continue
            if rule=='credential-url' and re.fullmatch(rb'\$\{[A-Za-z_][A-Za-z0-9_]*\}',value):continue
            if (rule,match.group(0)) in exemptions:continue
            if rule=='labelled-email' and re.search(rb'@(?:[^@.]+\.)*(?:example\.(?:com|org|net)|[^@.]+\.(?:invalid|test))$',value,re.I):
                continue
            found.append({'rule':rule,'line':data[:match.start()].count(b'\n')+1})
    return found


def plist_strings(value):
    def encode(item):
        if isinstance(item,bytes):return item.decode('utf-8',errors='replace')
        if hasattr(item,'isoformat'):return item.isoformat()
        raise TypeError('unsupported plist value')
    if isinstance(value,(dict,list)):
        # Preserve labels next to values, including nested XML/binary plist data.
        return [json.dumps(value,ensure_ascii=False,default=encode).encode('utf-8')]
    if isinstance(value,str):return [value.encode('utf-8')]
    if isinstance(value,bytes):return [value]
    return []


def linked_ancestor(path):
    # Canonical macOS system aliases are allowed; user-created aliases are not.
    aliases={'/tmp':'/private/tmp','/var':'/private/var','/etc':'/private/etc'}
    path=Path(path).absolute()
    return any(p.is_symlink() and not (str(p) in aliases and str(p.resolve())==aliases[str(p)])
               for p in [path,*path.parents])


def scan_roots(roots):
    files=[]; findings=[];errors=[]
    for label,root in roots.items():
        root_files=0
        root=Path(root)
        if linked_ancestor(root) or not root.is_dir():
            errors.append({'root':label,'reason':'missing-or-linked-root'});continue
        entries=[]
        def walk_error(error):
            errors.append({'root':label,'reason':'unreadable-directory'})
        for directory,dirs,names in os.walk(root,followlinks=False,onerror=walk_error):
            entries.extend(Path(directory)/name for name in dirs+names)
        entries.sort()
        for path in entries:
            relative=path.relative_to(root).as_posix()
            path_id=digest(relative.encode('utf-8'))
            if linked_ancestor(path):
                errors.append({'root':label,'path_id':path_id,'reason':'symlink-not-scanned'});continue
            if path.is_dir():continue
            try:
                if not path.is_file() or path.stat().st_size>MAX_BYTES:raise ValueError()
                raw=path.read_bytes()
                if len(raw)>MAX_BYTES:raise ValueError()
                variants=[raw]
                if raw.startswith((b'\xff\xfe',b'\xfe\xff')):variants.append(raw.decode('utf-16').encode())
                if path.suffix=='.plist' or raw.startswith(b'bplist00'):
                    variants.extend(plist_strings(plistlib.loads(raw)))
                root_files+=1
                files.append({'root':label,'path_id':path_id,'sha256':digest(raw),'bytes':len(raw)})
                exemptions=set()
                if (label=='backend-source' and relative=='tests/reviewed-publish.test.cjs'
                    and digest(raw)==NEGATIVE_URL_FIXTURE_SHA256):
                    exemptions.add(('credential-url',b'https://user:password@'))
                    files[-1]['reviewed_exemption']='negative-source-url-fixture-v1'
                hits={ (hit['rule'],hit['line']) for data in [*variants,relative.encode('utf-8')] for hit in matches(data,exemptions) }
                findings.extend({'root':label,'path_id':path_id,'rule':rule,'line':line}
                                for rule,line in sorted(hits))
            except (OSError, ValueError, TypeError, OverflowError, RecursionError, plistlib.InvalidFileException):
                errors.append({'root':label,'path_id':path_id,'reason':'unreadable-oversized-or-invalid-file'})
        if not root_files:errors.append({'root':label,'reason':'empty-required-root'})
    return {'schema_version':1,'policy':POLICY_VERSION,'status':'ERROR' if errors else 'FAIL' if findings else 'PASS',
            'scope':'literal-credentials-and-labelled-pii','files':files,'findings':findings,'errors':errors}


def main():
    parser=argparse.ArgumentParser(description='Scan fixed run inputs without printing matched values')
    parser.add_argument('--run',required=True,type=Path)
    args=parser.parse_args();run=args.run.absolute()
    roots={'app-source':run/'source/app','backend-source':run/'source/backend',
           'fixtures':run/'source/backend/data','logs':run/'logs',
           'app-bundle':run/'build/app/work/DerivedData/Build/Products/Debug-iphonesimulator/GODIEOR.app'}
    result=scan_roots(roots)
    (run/'secret-findings.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ['schema_version','policy','status','scope']} |
                     {'files':len(result['files']),'findings':len(result['findings']),'errors':len(result['errors'])}))
    return 3 if result['status']=='ERROR' else 1 if result['status']=='FAIL' else 0


if __name__=='__main__':sys.exit(main())
