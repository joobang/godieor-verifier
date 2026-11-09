# Evidence v2 · 전체 대상 조합 바인딩

v1 호환 입력은 앱 전용이다. v2는 앱·backend·API 계약·migration·acceptance·verifier 상태 조합을 모든 check/review에 연결한다. 실제 파일 존재·실행·격리 진위는 후속 runner가 확인하며 이 parser는 입력 선언만 검증한다.

v1 필드에 다음을 추가한다.

- schema_version: 2.
- backend: 정확히 base_sha/head_sha (40자리 소문자 hex).
- contract: 정확히 version/sha256. sha256은 고정 backend 계약 manifest 파일의 원본 bytes SHA256.
- migrations: 정확히 sha256. 이는 migration 파일 집합의 manifest digest다. runner는 상대 경로 POSIX 문자열을 키로, 원본 파일 SHA256을 값으로 한 dict를 만들고 아래 canonical JSON 규칙으로 hash한다. 빈 디렉터리는 `{}` digest, 존재하지 않는 디렉터리는 runner 오류. 파일 내용/추가/삭제/이름 변경은 모두 manifest가 달라진다. 이번 단계는 파일 집합을 직접 수집하지 않는다.
- 각 checks 원소: subject_sha256 추가.
- review: subject_sha256 및 run_id 추가. review-v2.schema.json 참조.

subject_sha256은 다음 6개 필드만 가진 dict의 SHA256이다: app, backend, contract, migrations, acceptance, verifier. 각 내부 필드 집합은 parser가 엄격하게 제한한다. 모든 check/review가 같은 digest를 참조한다. 기존 check의 run_id/app_head_sha/acceptance_sha256, review의 app_head_sha/acceptance_sha256 검사도 유지한다.

canonical JSON은 Python json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')를 사용한다. ASCII 고정 SHA 및 필드명이 중심이며 별도 Unicode 정규화를 하지 않는다. subject.subject_digest 함수가 공통 계산 지점이다. v1으로 schema만 내리고 backend/contract/migrations 또는 v2 binding을 남긴 입력은 거부한다. v1에 v2 필드가 없으면 기존 앱 전용 집계만 수행한다.

report envelope schema_version은 기존 1을 유지한다. evidence_schema_version 필드에 입력의 1/2를 추가하며 원본 evidence와 원본 bytes digest도 유지한다. 따라서 v1 성공을 v2 통합 결과로 승격하지 않는다.

```sh
./scripts/verifier --acceptance requirements/acceptance.yaml --evidence examples/evidence-v2.json --require-schema-version 2 --out work/demo-v2
```

예제는 전부 가상이다. 현재 draft/fixture/미확인 격리로 REVIEW_REQUIRED(exit2)가 정상이다. acceptance 승인·대상별 검사 실행 여부는 이 형식 추가로 자동 충족되지 않는다. 사용자가 임의 hash/binding을 다시 계산하는 것을 막는 서명·원격 증명 체계는 아니다. 환경/기준/조합 바인딩과 증거 진위를 구분한다.

호출자 정책: 통합 실행은 `--require-schema-version 2`를 반드시 지정한다. Python API는 assess/report의 required_schema_version=2를 사용한다. 기본값1은 v1 앱 전용 호환 모드다. v2 필드를 모두 제거한 입력은 정상 v1과 구별할 수 없으므로 evidence 자체 선언만으로 downgrade를 막는다고 주장하지 않는다. report의 required_schema_version과 evidence_schema_version을 함께 확인한다. 통합 runner가 최소schema2를 강제하는 것은 VFY-04의 필수 조건이다.
