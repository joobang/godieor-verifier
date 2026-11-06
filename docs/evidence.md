# Evidence v1

`examples/evidence.json`은 가상 입력이다. 제품 실행 결과가 아니다.
engine은 JSON을 읽으며 바이너리나 앱 코드를 실행하지 않는다.

필수 입력:

- `schema_version`: 1.
- `run_id`, `started_at`, `finished_at`: 실행 식별자, timezone을 포함한 ISO 8601 시각.
- `app.base_sha`, `app.head_sha`: 40자리 Git SHA.
- `verifier.sha`: 40자리 SHA 또는 초기 미커밋이면 null.
- `verifier.dirty`, `verifier.state_sha256`: 미커밋 상태와 검증기 상태 SHA-256.
- `acceptance.version`, `acceptance.sha256`: 읽은 acceptance 파일과 정확히 일치해야 함.
- `execution.mode`: `fixture` 또는 `external-runner`.
- `execution.isolation_verified`: 실제 격리 검사 여부. 자체 선언만으로 신뢰하지 않음.
- `checks`: 각 검사에 run_id·app_head_sha·acceptance_sha256 binding,
  check ID, PASS/FAIL/ERROR/SKIPPED, argv 배열, exit code,
  started_at/finished_at, evidence 경로(로그/artifact URI 또는 파일 경로).
- `review`: COMPLETE/PENDING/ERROR, 대상 app SHA·acceptance hash, model, settings,
  started_at/finished_at, findings. PENDING/ERROR에서는 model과 시각은 null 허용.
- finding: id, requirement_id, severity, evidence, reproduction, uncertainty.

engine은 입력 binding·형식·필수 검사·종료 코드를 확인한다.
로그 파일 존재/내용·실제 명령 실행·격리 동작의 진위는 후속 runner가 보장할 영역이다.
임의 evidence를 넣어 나온 PASS는 제품 승인 근거가 아니다.

출력에는 acceptance 실제 digest, 원본 evidence SHA-256, 전체 입력, 판정 시각과 reasons를 포함한다.
진위가 확인된 runner와 연결되기 전에는 검증 시스템을 운영용으로 사용하지 않는다.
