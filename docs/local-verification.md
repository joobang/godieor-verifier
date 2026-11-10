# 기존 Mac 계정에서 검증 (현재 정책)

2026-11-10 사용자 확정: godieorbuild 전용 계정 방식 폐기. 계정 전환/su/암호 입력과 Foundation/Darwin T 격리 진단을 제품 개발·출시의 선행조건으로 두지 않는다. 계정 생성·삭제·HOME ACL·키체인 설정은 이 변경에서 건드리지 않는다. 과거 계정/ACL 기록은 이력이며 재개 지시가 아니다.

## 유지하는 검사

- 고정 Git base/head와 원시 tree/blob snapshot, 별도 build 사본. dirty/untracked 제외 표시.
- 앱·backend 계약manifest 대조, migration 집합 digest, 기준/verifier state와 모든 결과의 v2 subject binding.
- backend 최소 환경/sandbox, 실제 compile/자체검사 및 기존DB와 분리된 일회용PostgreSQL migration/반복수집/API smoke. 단계별exit·시각·로그hash.
- iOS는 기존 계정에서 검증기 소유의 고정 xcodebuild argv로 generic Simulator Debug·CODE_SIGNING_ALLOWED=NO 빌드. 제품의 shell 빌드 스크립트를 실행하지 않는다. 실행기 환경은 최소HOME/임시cache를 쓰지만 OS권한격리로 보장하지 않는다. Xcode project build phase도 실행코드이므로 검토한 본 프로젝트의 고정 source에 사용한다.
- 독립 리뷰는 구현대화와 별도컨텍스트. 승인초안/미실행/실패는 그대로 기록한다.

전용계정 진단 scripts/probe-dedicated-ios 및 check-isolated-ios-host와 Python module CLI는 폐기 안내 후exit2. 전환·인증·설정 변경을 수행하지 않는다. 과거 순수진단함수/회귀기록은 재발방지 이력으로 보존한다.

## 실행

```sh
./scripts/runner --app /path/godieor-app --app-base APP_BASE_SHA40 --app-head APP_HEAD_SHA40 \
 --backend /path/godieor-backend --backend-base BE_BASE_SHA40 --backend-head BE_HEAD_SHA40 \
 --acceptance requirements/acceptance.yaml --out /private/tmp/godieor-NEW-RUN \
 --execute --fetch-dependencies --node /absolute/path/to/node24 \
 --npm-cli /absolute/path/to/npm/bin/npm-cli.js --npm-cache /path/to/npm-cache
```

준비만 할 때는 --execute와 도구 옵션을 생략한다. 출력디렉터리는 새경로만 사용한다. --fetch-dependencies는 npm ci(ignore-scripts)와 Prisma생성 준비단계에만 외부망, 실제DBsecret은 이후 일회용DB 단계에서 주입한다. 운영키/.env/Apple ID/서명인증서를 빌드사본으로 복사하지 않는다.

steps.json의 execution_policy는 backend sandboxed/iOS local-reviewed로 구분한다. evidence.execution.tool_versions.ios_execution_policy와 isolation_verified=false도 남긴다. 서명없는빌드 성공은 iPhone 설치/Google로그인/실데이터coverage/모든사용자흐름 통과의 증거가 아니다.

엔진의 기준·필수검사·승인규칙은 낮추지 않았다. 실행한 ios-build와 INT-01A의 event-identity/time-semantics API component를 실제 결과로 연결한다. 필터는 최신정책/이전초안차이로 성공해도부분관찰 SKIPPED, 미실행기준도 SKIPPED, review는 PENDING. 상세 docs/api-checks.md. 때문에 모든 실행단계가 성공해도 전체report는 ERROR일 수 있다. 단계별 성공과 제품통합PASS를 구분한다. 현재 acceptance draft라 공식 제품승인 없음.

P5(setsid 후손)와 완전OS격리는 이 로컬 개발 검사에서 해결한 것으로 취급하지 않는다. 전용계정 방식으로 돌아가려는 후속과제는 폐기했다. 신뢰하지 않는 외부PR 코드의 무인실행 환경은 별도 범위다. 현재 제품기능/데이터연동 작업은 이 격리과제에 종속되지 않는다.
