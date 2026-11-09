# 로컬 snapshot·실행기 (VFY-03/04 초기 구현)

`scripts/runner`는 **로컬 macOS 초기 실행기**다. 전체 승인 검사·AI 호출 어댑터·완전한 후손 프로세스 수명 격리는 미완료다. 제품 PASS를 활성화하는 시스템이 아니다.

## 준비

고정 40자리 base/head SHA 2쌍과 acceptance 경로, 아직 없는 출력 디렉터리를 지정한다. 기본 모드는 준비만 수행하며 미실행 검사를 SKIPPED로 채워 ERROR(exit3)를 반환한다. 준비 성공을 제품 통과로 오해하지 않는다.

```sh
./scripts/runner --app /path/godieor-app --app-base APP_BASE_SHA40 --app-head APP_HEAD_SHA40 \
  --backend /path/godieor-backend --backend-base BE_BASE_SHA40 --backend-head BE_HEAD_SHA40 \
  --acceptance requirements/acceptance.yaml --out /private/tmp/godieor-new-run
```

Git 실행은 고정 /usr/bin/git, 최소환경, fsmonitor/hooks/replace ref·lazy fetch 비활성화 및 모든 Git transport 금지로 수행한다. **Git archive 대신 raw ls-tree/cat-file blob**을 추출한다. 로컬 info/attributes·export-ignore/export-subst가 고정 commit 내용을 변경하지 않게 하기 위해서다. symlink/submodule/특수파일, 미해결 LFS 포인터, 경로탈출과 Unicode·대소문자 충돌은 거부한다. snapshot manifest의 각 파일 및 전체tree hash를 기록한다. 미커밋/untracked 파일은 제외하고 그 여부를 명시한다. 원본 snapshot과 writable build 사본을 분리하고 chmod는 편의적인 보호이며 OS 격리 증명이 아니다.

실행 모드에는 다음을 추가한다.

```sh
--execute --node /absolute/path/to/node24 --npm-cli /absolute/path/to/npm/bin/npm-cli.js \
  --npm-cache /path/to/npm-cache
```

캐시 `_cacache`를 실행 전용 HOME에 복사해 offline npm ci --ignore-scripts를 실행한다. 캐시에 없으면 실패한다. 필요한 경우 `--fetch-dependencies`는 **의존성 설치·Prisma 엔진 생성 준비 단계에만** 외부망을 허용한다. registry는 공식 npm, user/global config는 새 빈 파일, 실제 DB 주소/키는 이 단계에 전달하지 않는다(Prisma config 로딩에는 접속 불가능한 생성 전용 URL만 제공). 이후 컴파일·검사·실제DB 실행은 loopback 망만 허용한다. 제품 Node24와 npm 도구 경로는 사용자가 신뢰하는 설치본을 지정한다.

macOS sandbox-exec 기본거부 프로필에서 빌드/임시 HOME만 쓰기, snapshot과 시스템·도구 경로 읽기를 허용한다. 원래 HOME/.env/운영키·Docker socket을 제품 프로세스에 전달하지 않는다. Docker 제어는 실행기의 고정 인자로 수행한다. 생성한 가상 canary 읽기 거부, 제품 원본 읽기 거부, snapshot 읽기 허용/쓰기 거부, 임시HOME 쓰기 허용을 probe한다. 이 제한된 probe 성공도 전체 권한격리 검증은 아니며 **isolation_verified=false를 유지**한다. /Library·/opt/homebrew 등 시스템 도구 디렉터리의 세부 비밀 분류까지 검증하지 않았고, 메타데이터 조회는 허용한다.

**iOS 제한 빌드 현황(2026-11-09):** macOS Foundation의 atomic plist 쓰기는 `TMPDIR`을 별도 HOME으로 설정해도 사용자별 Darwin 임시 디렉터리의 실제 경로 `/private/var/folders/.../T`에 쓰기 권한이 없으면 EPERM이 발생한다. 같은 경로를 진단용으로 허용하면 `DerivedData/info.plist`·`LogStoreManifest.plist` 오류가 사라지고 Xcode 컴파일/링크까지 진행하지만 이후 `swbuild.tmp.*` 오류 등으로 exit65가 계속된다. 이 사용자 공유 T 디렉터리를 runner sandbox에 허용하면 다른 작업의 임시 파일까지 접근할 수 있으므로 정식 프로필에서는 허용하지 않는다. 실제 보안 경계를 보존하려면 별도 사용자/격리된 환경에서 Xcode를 실행하는 방안을 먼저 검토해야 한다. 해당 방법은 아직 구현·검증되지 않았다.

전용 실행 사용자/VM의 권한·수명 요구사항과 실패 재현 게이트는 [runner-isolation.md](runner-isolation.md)를 따른다. 전용 UID 분리만으로 `setsid` 후손이 제거되는 것은 아니다.
전용 사용자 사전점검 도구 `scripts/check-isolated-ios-host`는 실행 환경의 기초 조건만 점검하며 검사 성공만으로 빌드·격리 성공을 선언하지 않는다.

## 실행·결과

고정 recipe: 경계 probe → dependency 설치 → Prisma generate → tsc → backend 자체 tests → digest 고정 PostgreSQL tmpfs/임시 loopback port → migrate → 독립 DB smoke → iOS generic Simulator build. 기존 제품 DB·포트·볼륨은 사용하지 않는다. DB password/커서 키는 매번 임시 생성하고 runner 출력에 쓰지 않는다. 마이그레이션 manifest는 모든 파일 상대경로/digest의 canonical JSON hash다. 앱의 계약 참조와 backend 계약manifest/파일을 대조한다.

단계별 argv·exit code·시각·timeout·로그 SHA256을 steps.json에 기록한다. DB smoke는 가상 데이터 반복 ID·Nest DI·달력/상세 기본 연결 검사이며 모든 GD 요구사항을 충족하는 독립 통합 suite가 아니다. 실행한 ios-build는 종료코드/timeout에 따라 PASS·FAIL·ERROR로 매핑하고 나머지 필수 검사는 SKIPPED로 둔다. reviewer는 PENDING이며 결과를 생성하지 않는다. runner는 evidence v2를 생성하고 최소schema2로 집계한다. `report.json/md`는 기본적으로 ERROR(미실행 필수 검사)다.

실행 오류는 runner-error.json과 steps/log에 남긴다. 출력 디렉터리는 재사용/덮어쓰지 않는다. 로그는 로컬 실행 산출물로 보존하고 이 초기 구현에서는 source tree와 함께 `work/` 또는 /private/tmp에 둔다. 실제 인증 데이터가 있는 임의 코드를 실행하도록 설계한 시스템이 아니다.

## 수명·보안 한계

timeout 또는 정상 종료 후 최초 프로세스 그룹을 정리한다. **자식이 setsid로 별도 세션으로 이탈하면 이 방식으로 완전 제거를 보장할 수 없다.** 독립 리뷰에서 가상 자식으로 재현한 미해결 항목이다. 자식도 sandbox 제한은 상속하지만 전체 자원/수명 격리는 별도 컨테이너·전용 사용자/실행 서비스 설계가 필요하다. 임의 비신뢰 제품 코드를 안전하게 실행할 준비가 끝났다고 해석하지 않는다.

DB는 실행 시도부터 고유 이름으로 finally 정리한다. Docker CLI timeout 뒤에도 삭제를 시도한다. 강제 호스트 종료/전원 손실 때의 재시작 청소는 후속이다. 입력이 잘못돼 snapshot 준비부터 실패하면 ERROR로 끝나고 부분 출력 디렉터리는 진단용으로 남는다. 실행 명령과 로그가 실제로 생성됐다는 사실도 OS 격리·검증 기준 승인·통합 제품 PASS를 대신하지 않는다.
