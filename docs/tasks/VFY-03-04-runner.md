# VFY-03/04 · 고정 snapshot과 실행기
- 상태: 사용자 요청으로 구현 중단·인계 대기. 담당 codex-runner-01 해제. 초기 구현/부분 실행이며 전체 완료 아님.
- 기준: verifier ea96c2f, app f662344, backend89a6b48. 요구사항 VFY-03/04, GD-001~010 초안.
- 범위: 안전한 Git archive 추출/별도 build 사본/파일 manifest, 최소환경·timeout·로그 수집, 일회용DB 수명, evidence v2+최소schema2 집계.
- 실패 사례: symlink/경로탈출/submodule/LFS, dirty 원본 혼입, timeout·누락 검사·리뷰대기, 원본/비밀 접근, 정리 실패.
- LEARN-ID: LEARN-0014 예정. 승인 기준 수정·통합PASS 선언 없음.

## 진행 기록
- raw Git tree/blob 추출로 전환. 독립 리뷰에서 Git fsmonitor 실행·replace ref/로컬 export속성·대소문자충돌·누락object remote helper 실행을 가상 marker로 재현했고 설정/환경·transport차단·원시blob추출로 수정. 회귀62개 통과.
- Docker run 응답 timeout 시에도 고유 이름으로 정리 시도하도록 수정. 최초processgroup만 정리하므로 setsid 후손 수명 전체격리는 미완료. VFY-03 전체완료나 제품PASS로 표시하지 않는다.
- 실제 macOS sandbox: 최소profile 기동실패(-6) 진단 후 루트디렉터리 자체읽기 literal권한으로 기동 성공. 원본읽기거부·snapshot쓰기거부·snapshot읽기/임시HOME쓰기 허용 probe 통과.
- 실제 고정source에서 dependency 설치 성공. offline캐시부족→별도빈 npm설정파일 적용→Prisma generate의 DATABASE_URL 누락→생성전용 dummyURL→엔진다운로드 필요를 순차 진단. bootstrap(의존성/Prisma생성)만 외부망, 실제DBsecret 미전달. 생성 이후는 loopback 제한.
- 실행 결과는 /private/tmp/godieor-vfy-run-*의 source/build/steps/logs/evidence/report에 보존. 실행 중 최신run 경로는 /private/tmp/godieor-last-run-path 로컬 포인터. 이 임시 포인터는 source나 승인 근거가 아니다.

## 실행 확인과 남은 항목
- 2026-11-09, /private/tmp/godieor-vfy-run-d630d3c9: Node24.19.0, 경계probe/dependencies/Prisma generate/tsc/backend47tests/migrate/database-smoke 모두 exit0, iOS generic build exit65. 해당 일회용 컨테이너는 종료 후 docker ps에서 남아 있지 않음을 확인했다.
- shell의 build 사본 mkdir/touch는 동일 sandbox에서 성공하지만 Xcode는 DerivedData 정보 쓰기를 거부당한다. /tmp별칭 추가만으로 해결되지 않았다. 실제 iOS 제한실행 성공으로 표시하지 않는다.
- 실행된 iOS 실패를 SKIPPED로 숨기지 않도록 save에서 FAIL/ERROR를 실제 단계exit/timeout에 따라 보존했다. 다른 미실행필수검사는 SKIPPED 유지.
- 독립 reviewer Peirce(01a1bf1e-ad14-7353-9f4c-e3dbcaa85c18, fork_context=false)는 Git보안수정·추가62개검사 및 remotehelper 대조실험을 확인했다. setsid후손수명P5는 미해결, reviewer는 실제sandbox실험을 독립실행하지 않았다.
- LEARN-0014: docs/learning/entries/0014-snapshot-and-local-runner.md. VFY-03/04는 초기구현/부분실행 상태이며 전체완료가 아니다. 다음 우선순위는 제한 Xcode 빌드와 후손수명격리 해결 후 전체실행·AI입출력어댑터/필수검사연결이다.


## 다음 계정 인계 · 2026-11-09 KST

사용자가 토큰 부족으로 이 지점에서 중단·문서정리·다른 계정 인계를 요청했다. 새 기능 작업은 시작하지 않는다.

- 구현 파일: src/godieor_verifier/{snapshot.py,runner.py,database-smoke.cjs}, scripts/runner, tests/test_runner.py. 사용법 docs/runner.md.
- verifier 브랜치 codex/vfy-03-runner, 제품 app 브랜치 codex/app-01-review-fixes, backend dev. 인계 최종 SHA는 Git HEAD와 웹 전달본에서 확인. 이 작업 전 verifier ea96c2f, app f662344, backend89a6b48.
- 최종 실제 실행: /private/tmp/godieor-vfy-run-391f70fd. 요약/로그 사본은 verifier work/handoff/godieor-vfy-run-391f70fd (Git 제외). 원본 evidence는 verifier ea96c2f + dirty/state digest로 기록된 당시 결과이며 새 커밋의 결과로 재라벨하지 않는다. snapshot/build 원본은 /private/tmp에만 있으며 지워지면 새 run 필요.
- 마지막 명령 scripts/self-test.sh: 62개 성공. backend 고정사본47개 자체검사 및 일회용 DB migration/반복수집/달력·상세 smoke 성공. source read허용·원본read거부·sourcewrite거부·HOMEwrite허용 probe 성공. 마지막 컨테이너 docker ps name=godieor-vfy- 결과 없음.
- iOS 제한빌드 exit65. shell mkdir/touch는 build 사본에서 성공했지만 Xcode의 DerivedData/info.plist 및 LogStoreManifest 쓰기는 EPERM. /tmp·/private/tmp 별칭, CFFIXED_USER_HOME, clangcache 경로 조정만으로 해결 안 됨. sandbox를 무조건 풀어 성공으로 대체하지 말고 Xcode 프로세스/XPC/파일권한 원인을 좁힌다.
- 독립리뷰 P5 미해결: setsid로 새 세션을 만든 후손은 최초 process group 정리를 벗어난다. timeout은 최초group만 보장. 전용 실행 서비스/컨테이너/사용자 등 수명격리 설계 필요. isolation_verified=false 유지.
- 그 밖의 미완료: 자동 AI review 어댑터, 모든 acceptance check별 독립 검사 연결, 전체 통합 실행/승인. 기본 준비모드/부분실행은 SKIPPED로 ERROR가 정상. 실패한 iOS는 FAIL 기록 유지. acceptance 원본/승인 상태 그대로.
- reviewer Peirce 최종 추가 실행코드 지적 없음(위 P5 여전히 open). 초기 P1 Git fsmonitor/replace/attributes/missingobject helper·경로충돌 및 DB timeout 정리 지적을 수정했고 reviewer는 62개검사·remotehelper 대조실험까지 확인했다. 실제 sandbox/build/DB는 작성자 실행이며 reviewer 독립실행 아님.

### 다음 작업 순서

1. AGENTS → docs/system/status.md → handoff.md → 본 카드 → docs/runner.md. 세 저장소 HEAD/branch/dirty를 확인하고 다른 세션의 동시 수정이 없는지 확인한다.
2. work/handoff/.../steps.json·report.json·logs/ios-build.log를 읽는다. VFY-03/04 전체 완료/제품 PASS로 오해하지 않는다.
3. 우선 Xcode 제한빌드 EPERM 원인을 좁힌다. 새 outfile을 사용해 재실행하고 기존 evidence를 덮어쓰지 않는다. 후손수명격리를 해결할 수 없다면 open finding으로 유지하고 신뢰할 수 없는 임의 코드 실행에 사용하지 않는다.
4. 의미 있는 코드 변경 후 자기검사·분리 컨텍스트 리뷰, 실제 실패 경로 재현, 카드·공통사본·학습기록 업데이트. 승인 기준은 임의로 승인하지 않는다.

### 2026-11-09 후속 진단 · VFY-03/04 (codex-eprem-02)

- 재개 시 app `codex/app-01-review-fixes` HEAD `7c868d9`, verifier `codex/vfy-03-runner` HEAD `1cb7c9d`, backend `dev` HEAD `2a9d06f`이며 각 checkout은 clean. 이전 기록의 HEAD를 새 실행의 binding으로 재사용하지 않는다.
- 기존 `/private/tmp/godieor-vfy-run-391f70fd/build/app` 사본에서 `runner.profile()`을 사용한 최소 재현을 실행했다. 현재 Codex 외부 sandbox 아래에서 중첩 `sandbox-exec`은 `sandbox_apply: Operation not permitted`(exit 71)였고, 승인된 제한 실행 환경에서 동일 재현이 가능했다.
- 제한 프로필에서 셸의 임시 HOME 및 DerivedData/Logs/Build 파일 쓰기는 exit 0. `xcrun --find xcodebuild`와 `xcodebuild -version`도 exit 0이나 `/var/folders/.../T/xcrun_db-*` 캐시 생성 EPERM 메시지가 발생했다. `TMPDIR` 환경값은 임시 HOME 아래여도 xcrun은 이 경로에 접근했다.
- 앱 사본에서 동일 프로필로 `scripts/build-ios.sh`를 실제 실행하면 exit 65로 `LogStoreManifest.plist`/`DerivedData/info.plist` 쓰기 EPERM이 재현됐다. xcrun 캐시 경로 `/var/folders/gt/4z3x36157d3bq4256swptnsw0000gn/T`만 추가 쓰기 허용한 비교 실행도 exit 65였다. 따라서 xcrun 캐시만 해결해도 Xcode 빌드가 성공한다는 가설은 반증됐다.
- sandboxd 관련 unified log 쿼리는 해당 기간 거부 이벤트를 반환하지 않았다. Xcode 내부/XPC 권한·파일 작업 종류·경로 정규화 중 어느 것이 주원인인지는 미확정이다. 모든 실행은 기존 임시 build 사본 대상으로, 새 전체 runner/evidence 생성은 하지 않았다.
- `allow default` 등 광범위한 권한을 사용하는 추가 진단은 자동 승인 심사에서 거부되어 실행하지 않았다. 고정 runner 프로필은 완화하지 않았으며 `isolation_verified=false`, iOS 빌드 실패, P5 미해결, 통합 PASS 없음은 유지한다.
- 다음: 기존 임시 build 사본과 Xcode의 실제 경로를 대상으로 **필요한 권한만 제한적으로 확인**할 별도 승인된 진단을 설계한다. 승인 전에는 광범위 sandbox 완화를 실행하지 않는다.

### 2026-11-09 후속 재개 · Foundation atomic 쓰기 원인 분리 (codex-eprem-03)

- 기준 verifier `b1d5edd`, app `7c868d9`, backend `2a9d06f` (시작 상태 clean). VFY-03/04, GD-001~010 초안. 변경 범위는 sandbox 보안 경계 검사와 실행/원인 기록. 예상 실패는 임시 캐시 위치를 잘못 추정하거나 공유 임시 경로까지 열어 snapshot 격리를 훼손하는 것이다.
- `DerivedData`를 임시 HOME으로 이동하거나 `/private`, `/tmp` 등의 상위 디렉터리 literal 읽기 권한을 추가해도 Xcode exit65와 plist EPERM 동일.
- 임시 Objective-C/Foundation 진단 프로그램에서 같은 sandbox 아래 `NSDictionary writeToFile:atomically:NO`와 `NSData writeToURL` 성공, `atomically:YES`와 `NSDictionary writeToURL:error:` 실패. macOS 물리 경로 `/private/var/folders/gt/.../T` 쓰기 권한만 추가하면 atomic 저장 성공. `C`만 허용하면 실패. 기존 `/var/folders/.../T` 허용 시도는 물리 경로를 포함하지 않았다.
- T/C 두 디렉터리의 물리 경로와 별칭에 진단용 쓰기 허용 후 Xcode 재실행: 초기 DerivedData plist 오류 0건, 실제 컴파일 및 링커 단계 진입. 그러나 `swbuild.tmp.*`의 EPERM와 두 아키텍처의 링크 실패로 **exit65**. 로그 `/private/tmp/godieor-xcode-physical-cache.log` (임시 분석파일, 제품/evidence 아님). Xcode 제한 빌드 성공 확인은 아니다.
- 공용 사용자 임시 T 디렉터리 전체를 제품 프로세스에 허용하면 다른 앱/프로세스의 임시 자산을 수정할 위험이 있어 runner profile에는 반영하지 않음. runner 주석·테스트와 docs/runner.md 및 LEARN-0014에 한계 기록. Xcode 빌드의 별도 사용자/격리 환경 설계가 다음 해결 과제. P5 setsid 수명 격리, 전체 runner 및 통합 PASS 미해결 상태 유지.

재실행 예시(40자리 SHA는 원본 run의 evidence.json 또는 새로 확정한 조합을 사용):

```sh
./scripts/runner --app /Users/dojoohwan/workspace/godieor-app --app-base APP_BASE_SHA40 --app-head APP_HEAD_SHA40 \
  --backend /Users/dojoohwan/workspace/godieor-backend --backend-base BE_BASE_SHA40 --backend-head BE_HEAD_SHA40 \
  --acceptance requirements/acceptance.yaml --out /private/tmp/godieor-FRESH-RUN \
  --execute --fetch-dependencies \
  --node /private/tmp/godieor-npm-cache/_npx/09ae5d3560c7b1f2/node_modules/node/bin/node \
  --npm-cli /opt/homebrew/lib/node_modules/npm/bin/npm-cli.js --npm-cache /private/tmp/godieor-npm-cache
```

Node 도구/캐시가 없어졌으면 신뢰하는 Node24와 npm 경로를 새로 정하고 버전을 기록한다. 외부망은 준비 단계만 허용되며 실제 DB credential은 이후 일회용DB 단계에서만 주입한다. LEARN-0014에 실제 발견/가상회귀/미해결 격리를 구분해 남겼다.

### 2026-11-09 실행 경계 후속 설계 (codex-isolation-04)

- 시작 상태: verifier `aaad6a2` / `codex/vfy-03-runner`, app `7c868d9` / `codex/app-01-review-fixes`, backend `2a9d06f` / `dev`. 모두 clean. VFY-03/04·GD-001~010 초안, LEARN-0014 연결.
- 범위: 기존 제한 Xcode 로그를 재확인하고 전용 사용자/실행 서비스 또는 run별 VM 설계·재현 게이트를 `docs/runner-isolation.md`에 명문화. 예상 실패는 사용자별 공용 `T` 경로를 제품 sandbox에 개방하거나 전용 UID만으로 `setsid` 제거를 보장한다고 오인하는 것.
- 기존 `/private/tmp/godieor-xcode-physical-cache.log`에는 `swbuild.tmp.*`의 물리 경로 `/private/var/folders/.../T` EPERM과 xcrun 캐시 오류가 남아 있다. 새로운 Xcode 실행·전용 계정 생성은 하지 않았다.
- 문서 변경 뒤 `./scripts/self-test.sh` 62개 통과, `git diff --check` 성공. 실행 격리·Xcode 문제를 해결했다는 의미는 아니다.
- 다음: 전용 실행 ID의 최소 환경 마련 후 Foundation probe→제한 iOS 빌드→`setsid` timeout/강제종료 시나리오를 실제 검사. 어떤 방식도 아직 구현된 격리로 간주하지 않으며 `isolation_verified=false`, 기존 iOS exit65, P5 open 및 통합 PASS 없음 유지.

### 2026-11-09 전용 사용자 사전점검기 (codex-isolation-05)

- 시작: verifier `7e13407` / `codex/vfy-03-runner`, app `7c868d9` / `codex/app-01-review-fixes`, 작업 트리 clean. 요구사항 VFY-03/04, GD-001~010 초안, LEARN-0014.
- 변경: `scripts/check-isolated-ios-host`, `src/godieor_verifier/isolated_host.py`, 모의 환경 4개 검사. 실효 UID, OS 계정 HOME 및 물리 Darwin T의 소유권/접근 모드 사전 확인. 예상 실패: 개발 사용자와 UID/HOME 공유, 공유 T 디렉터리, root 실행, 임시 디렉터리 부재. 결과에는 항상 격리 미검증을 표시한다.
- 현재 UID 501에서 `--caller-uid 501 --caller-home /Users/dojoohwan` 실행: exit2, `same_uid_as_caller`, `home_overlaps_caller_home`; 물리 T 경로 관찰. 전용 macOS 계정 생성/전환이나 Xcode 재실행은 하지 않았다.
- `./scripts/self-test.sh`: 66개 통과. 문서/도구만으로 P5 종료·iOS 빌드·격리 PASS 없음. 전용 계정의 실환경 점검과 서비스 수명 검사가 후속이다.

### 2026-11-09 Foundation 재현 도구 (codex-isolation-06)

- 시작: verifier `7412e2b` / `codex/vfy-03-runner`, app `7c868d9` / `codex/app-01-review-fixes`, backend `2a9d06f` / `dev` 모두 clean. VFY-03/04, GD-001~010 초안, LEARN-0014. 범위는 전용 UID에서 재사용할 atomic plist 최소 재현 도구다.
- 추가: `scripts/foundation-atomic-probe.m`, `scripts/probe-foundation-atomic`. 고유 신규 출력 폴더에 합성 plist만 작성한다. 예상 실패는 Xcode 툴체인 접근 거부, sandbox 안의 임시 파일 생성 EPERM, 혹은 Foundation 비원자적/원자적 저장의 차이다.
- 현재 UID 501에서 `/private/tmp/godieor-foundation-probe-20261109-06` 일반 실행: `non_atomic=true`, `atomic=true`, exit0. 이 결과는 OS 격리 없이 실행한 기초 작동 확인이다.
- 동일 빌드 바이너리와 기존 runner 제한 프로필을 Codex 현재 sandbox 안에서 중첩 실행하면 `sandbox-exec: sandbox_apply: Operation not permitted`, exit71. Foundation 쓰기 결과는 관찰되지 않았다. 기존 승인된 제한 환경에서 과거 재현한 atomic EPERM을 이번 중첩 오류로 대체하거나 성공 처리하지 않는다.
- 검증: `./scripts/self-test.sh` 66개 통과, `git diff --check` 통과. 이 검사는 전용 UID 격리나 iOS sandbox 빌드 성공을 의미하지 않는다.
- 다음: 별도 UID/허가된 격리 실행 컨텍스트에서 동일 프로브 비교·실제 Xcode 빌드 및 P5 수명 검증. 격리 검증 false/통합 PASS 없음 유지.
