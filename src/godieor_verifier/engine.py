"""Deterministic evidence aggregation. Evidence authenticity belongs to the runner."""

from datetime import datetime, timezone
import hashlib
import json
import re

from .subject import validate_subject, subject_digest


EXIT_CODES = {"PASS": 0, "FAIL": 1, "REVIEW_REQUIRED": 2, "ERROR": 3}


class InvalidEvidence(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise InvalidEvidence(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def hexadecimal(value, length):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None


def timestamp(value):
    require(nonempty(value), "실행 시각 누락")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(parsed.tzinfo is not None and parsed.utcoffset() is not None, "시각에 timezone 필요")
    return parsed


def interval(item):
    start, end = timestamp(item["started_at"]), timestamp(item["finished_at"])
    require(start <= end, "종료 시각이 시작보다 빠름")


def validate_review_shape(review, version=1):
    """Enforce the review.schema.json contract without external dependencies."""
    fields = {"status", "app_head_sha", "acceptance_sha256", "model", "settings",
              "started_at", "finished_at", "findings"}
    if version == 2:
        fields |= {"subject_sha256", "run_id"}
    require(isinstance(review, dict) and set(review) == fields, "리뷰 필수/추가 필드 오류")
    require(review["model"] is None or isinstance(review["model"], str), "리뷰 model 형식 오류")
    for key in ("started_at", "finished_at"):
        require(review[key] is None or isinstance(review[key], str), "리뷰 시각 형식 오류")
    require(isinstance(review["settings"], dict), "리뷰 settings 형식 오류")
    require(all(type(x) in (str, int, float, bool, type(None)) for x in review["settings"].values()),
            "리뷰 settings 값은 JSON scalar여야 함")
    require(isinstance(review["findings"], list), "findings는 배열이어야 함")
    fields = {"id", "requirement_id", "severity", "evidence", "reproduction", "uncertainty"}
    for finding in review["findings"]:
        require(isinstance(finding, dict) and set(finding) == fields, "finding 필수/추가 필드 오류")
        require(all(nonempty(x) for x in finding.values()), "finding 문자열 누락/형식 오류")


def assess_check(check, required, seen, evidence, acceptance_digest):
    cid = check["id"]
    require(isinstance(cid, str) and cid in required and cid not in seen, "알 수 없거나 중복된 검사 ID")
    seen.add(cid)
    require(check["run_id"] == evidence["run_id"], cid + ": 실행 run ID 불일치")
    require(check["app_head_sha"] == evidence["app"]["head_sha"], cid + ": 검사 app SHA 불일치")
    require(check["acceptance_sha256"] == acceptance_digest, cid + ": 검사 acceptance digest 불일치")
    if evidence["schema_version"] == 2:
        require(check["subject_sha256"] == subject_digest(evidence), cid + ": 검사 subject 조합 불일치")
    status = check["status"]
    require(status in ("PASS", "FAIL", "ERROR", "SKIPPED"), "알 수 없는 검사 상태")
    if status in ("ERROR", "SKIPPED"):
        return "error", cid + ": " + status
    command = check["command"]
    require(isinstance(command, list) and bool(command) and all(nonempty(x) for x in command),
            cid + ": 실행 argv 누락")
    require(type(check["exit_code"]) is int, cid + ": 종료 코드 누락/형식 오류")
    require(nonempty(check["evidence"]), cid + ": 로그/artifact 근거 누락")
    interval(check)
    if status == "FAIL" or check["exit_code"] != 0:
        return "failure", cid + ": 검사 실패 (exit=%s)" % check["exit_code"]
    return "pass", ""


def assess(acceptance, evidence, acceptance_digest, required_schema_version=1):
    """Return a verdict; never infer executed checks from AI prose."""
    errors, failures, reviews = [], [], []
    try:
        require(type(evidence["schema_version"]) is int and evidence["schema_version"] in (1, 2),
                "지원하지 않는 evidence schema")
        require(type(required_schema_version) is int and required_schema_version in (1, 2), "요청 schema 정책 오류")
        require(evidence["schema_version"] >= required_schema_version, "요청한 최소 evidence schema 미충족")
        version = evidence["schema_version"]
        if version == 2:
            validate_subject(evidence, require, hexadecimal, nonempty)
        else:
            require(not ({"backend", "contract", "migrations"} & set(evidence)),
                    "v1은 backend/계약/migration 조합을 지원하지 않음")
            require(all("subject_sha256" not in check for check in evidence["checks"]),
                    "v2 binding을 v1으로 낮출 수 없음")
        require(nonempty(evidence["run_id"]), "run_id 누락")
        interval(evidence)
        for key in ("base_sha", "head_sha"):
            require(hexadecimal(evidence["app"][key], 40), "app SHA 형식 오류: " + key)
        verifier = evidence["verifier"]
        require(type(verifier["dirty"]) is bool, "verifier dirty 상태 누락")
        require(verifier["sha"] is None or hexadecimal(verifier["sha"], 40), "verifier SHA 형식 오류")
        require(verifier["sha"] is not None or verifier["dirty"], "미커밋 verifier는 dirty여야 함")
        require(hexadecimal(verifier["state_sha256"], 64), "verifier 상태 digest 누락")
        require(nonempty(acceptance["version"]), "acceptance 버전 누락")
        require(acceptance["status"] in ("draft", "approved"), "acceptance 승인 상태 오류")
        require(evidence["acceptance"]["version"] == acceptance["version"], "acceptance 버전 불일치")
        require(evidence["acceptance"]["sha256"] == acceptance_digest, "acceptance 파일 digest 불일치")

        required = acceptance["required_checks"]
        require(isinstance(required, list) and bool(required) and all(nonempty(x) for x in required),
                "필수 검사 목록이 비어 있거나 잘못됨")
        require(len(set(required)) == len(required), "필수 검사 ID 중복")
        requirements = acceptance["requirements"]
        require(isinstance(requirements, list) and bool(requirements), "요구사항 목록 누락")
        requirement_ids = set()
        covered = set()
        for requirement in requirements:
            rid = requirement["id"]
            require(nonempty(rid) and rid not in requirement_ids, "요구사항 ID 누락/중복")
            requirement_ids.add(rid)
            checks = requirement["checks"]
            require(isinstance(checks, list) and bool(checks), "요구사항 검사 연결 누락")
            require(all(isinstance(x, str) and x in required for x in checks), "알 수 없는 요구사항 검사 연결")
            require(nonempty(requirement["expectation"]), "요구사항 기대값 누락")
            covered.update(checks)
        require(covered == set(required), "요구사항과 연결되지 않은 필수 검사")

        execution = evidence["execution"]
        require(execution["mode"] in ("fixture", "external-runner"), "실행 mode 오류")
        require(type(execution["isolation_verified"]) is bool, "격리 검증 상태 누락")
        require(isinstance(execution["tool_versions"], dict) and bool(execution["tool_versions"]),
                "실행 도구 버전 누락")
        checks = evidence["checks"]
        require(isinstance(checks, list), "checks는 배열이어야 함")
        seen = set()
        for index, check in enumerate(checks):
            try:
                kind, reason = assess_check(check, required, seen, evidence, acceptance_digest)
                if kind == "error":
                    errors.append(reason)
                elif kind == "failure":
                    failures.append(reason)
            except (KeyError, TypeError, ValueError, OverflowError) as exc:
                errors.append("검사[%d] 입력 오류: %s" % (index, exc))
        errors.extend(cid + ": 필수 검사 누락" for cid in required if cid not in seen)

        review = evidence["review"]
        validate_review_shape(review, version)
        if version == 2:
            require(review["subject_sha256"] == subject_digest(evidence), "리뷰 subject 조합 불일치")
            require(review["run_id"] == evidence["run_id"], "리뷰 run ID 불일치")
        require(review["app_head_sha"] == evidence["app"]["head_sha"], "리뷰 app SHA 불일치")
        require(review["acceptance_sha256"] == acceptance_digest, "리뷰 acceptance digest 불일치")
        require(review["status"] in ("COMPLETE", "PENDING", "ERROR"), "리뷰 상태 오류")
        if review["status"] == "ERROR":
            errors.append("독립 AI 리뷰 실행 오류")
        elif review["status"] == "PENDING":
            reviews.append("독립 AI 리뷰 대기")
        else:
            require(nonempty(review["model"]) and isinstance(review["settings"], dict), "리뷰 모델/설정 누락")
            interval(review)
            findings = review["findings"]
            require(isinstance(findings, list), "findings는 배열이어야 함")
            finding_ids = set()
            for finding in findings:
                require(nonempty(finding["id"]) and finding["id"] not in finding_ids, "finding ID 누락/중복")
                finding_ids.add(finding["id"])
                require(finding["requirement_id"] in requirement_ids, "finding requirement ID 오류")
                require(finding["severity"] in ("critical", "high", "medium", "low"), "finding severity 오류")
                require(all(nonempty(finding[x]) for x in ("evidence", "reproduction", "uncertainty")),
                        "finding 근거/재현/불확실성 누락")
                reviews.append("미확정 AI finding: " + finding["id"])

        if acceptance["status"] != "approved":
            reviews.append("acceptance 미승인 초안")
        else:
            require(nonempty(acceptance["approved_by"]) and nonempty(acceptance["approval_record"]),
                    "승인 기록 누락")
            timestamp(acceptance["approved_at"])
        if execution["mode"] == "fixture":
            reviews.append("가상 evidence: 제품 실행 증거가 아님")
        if not execution["isolation_verified"]:
            reviews.append("실제 실행 권한 격리 미검증")
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        errors.append("입력 오류: " + str(exc))

    verdict = "ERROR" if errors else "FAIL" if failures else "REVIEW_REQUIRED" if reviews else "PASS"
    return {"verdict": verdict, "errors": errors, "failures": failures, "review_required": reviews}


def strict_json(data):
    def object_from_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "JSON 중복 키: " + key)
            result[key] = value
        return result

    def invalid_constant(value):
        raise InvalidEvidence("JSON 비표준 숫자: " + value)

    value = json.loads(data.decode("utf-8"), object_pairs_hook=object_from_pairs,
                       parse_constant=invalid_constant)
    # Escaped isolated surrogates can survive json.loads but cannot be UTF-8 reports.
    json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    return value


def report(acceptance_bytes, evidence_bytes, required_schema_version=1):
    acceptance_digest = digest(acceptance_bytes)
    evidence = None
    try:
        acceptance, evidence = strict_json(acceptance_bytes), strict_json(evidence_bytes)
        result = assess(acceptance, evidence, acceptance_digest, required_schema_version)
    except (ValueError, UnicodeError, RecursionError) as exc:
        evidence = None
        result = {"verdict": "ERROR", "errors": ["JSON 입력 오류: " + str(exc)],
                  "failures": [], "review_required": []}
    return {"schema_version": 1, "required_schema_version": required_schema_version, "evidence_schema_version": evidence.get("schema_version") if isinstance(evidence, dict) else None, "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "acceptance_sha256": acceptance_digest, "evidence_sha256": digest(evidence_bytes),
            "evidence": evidence, **result}


def markdown(result):
    lines = ["# GODIEOR verification", "", "Verdict: **%s**" % result["verdict"], "",
             "Evaluated: " + result["evaluated_at"], "",
             "Acceptance SHA-256: `" + result["acceptance_sha256"] + "`", "",
             "Evidence SHA-256: `" + result["evidence_sha256"] + "`", "",
             "입력 evidence를 집계한 결과다. 실제 실행·격리 진위는 별도 신뢰 경계에 속한다.", ""]
    for key in ("errors", "failures", "review_required"):
        if result[key]:
            lines.extend(["## " + key, ""] + ["- " + x for x in result[key]] + [""])
    lines.extend(["## Evidence", "", "```json", json.dumps(result["evidence"], ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)
