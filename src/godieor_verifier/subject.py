"""Version 2 subject binding. This validates declarations, not artifact authenticity."""
import hashlib
import json


def subject_digest(evidence):
    subject = {key: evidence[key] for key in
               ('app', 'backend', 'contract', 'migrations', 'acceptance', 'verifier')}
    return hashlib.sha256(json.dumps(subject, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def validate_subject(evidence, require, hexadecimal, nonempty):
    """Reject incomplete or ambiguous declarations before calculating their binding."""
    shapes = {'app': {'base_sha', 'head_sha'}, 'backend': {'base_sha', 'head_sha'},
              'contract': {'version', 'sha256'}, 'migrations': {'sha256'},
              'acceptance': {'version', 'sha256'},
              'verifier': {'sha', 'dirty', 'state_sha256'}}
    for key, fields in shapes.items():
        value = evidence[key]
        require(isinstance(value, dict) and set(value) == fields, key + ': subject 필드 오류')
    for key in ('app', 'backend'):
        for field in ('base_sha', 'head_sha'):
            require(hexadecimal(evidence[key][field], 40), key + ': SHA 형식 오류')
    require(nonempty(evidence['contract']['version']), '계약 버전 누락')
    for key in ('contract', 'migrations', 'acceptance'):
        require(hexadecimal(evidence[key]['sha256'], 64), key + ': digest 형식 오류')
