> **폐기된 실행방식 · 2026-11-10**: 전용 계정 방식은 사용자 지시로 종료. 아래는 당시 이력이며 재개 지시가 아니다. 현재 원본: [local-verification.md](local-verification.md).

# VFY-03/04 · macOS iOS 빌드 실행 경계 설계·부분 진단 구현

상태: 설계/운영 전제 검토. 요구사항 VFY-03/04, GD-001~010 초안. 승인된 격리 또는 제품 통합 PASS가 아니다.

## 관찰한 장애와 경계

2026-11-09 현재 실행기는 호출자 UID 501의 `sandbox-exec` 안에서 빌드한다. `TMPDIR`과 `HOME`을 각 run 아래로 돌려도 Foundation `atomically:YES`는 실제 Darwin 임시 경로 `/private/var/folders/.../T`를 사용했다. 그 물리 경로를 진단용 프로필에 허용하면 plist 원자적 저장이 성공하고 Xcode가 컴파일/링크까지 진입했지만 `swbuild.tmp.*` EPERM으로 exit65였다. 이는 개별 쓰기 실패에 대한 원인 분리이며 Xcode 전체의 성공이나 격리 증명이 아니다.

현재 UID의 공유 `T` 디렉터리를 정식 프로필에서 허용하면 같은 사용자의 다른 프로세스 임시 파일을 건드릴 수 있다. 해당 경로에 ACL만 추가하거나 `/var/folders` 별칭만 허용하는 변경은 보안 목표를 충족하지 못한다. `TMPDIR`만 지정하는 방식도 실제 실험으로 반증됐다.

## 선택한 실행 모델 (2026-11-10 사용자 확정)

사용자는 **빌드 전용 표준 macOS 사용자** 방식을 선택했다. 단일 run 실행 서비스는 구현 제안이며 아직 미구현이다. 계정 생성 절차는 [dedicated-account-setup.md](dedicated-account-setup.md)를 따른다. 이 사용자는 기존 개발 사용자와 UID/HOME/Darwin 임시 경로가 달라야 하고 운영 계정/키체인/소스 저장소/호스트 Docker socket/네트워크 자격 증명에 접근할 수 없어야 한다. 서비스가 고정 SHA에서 만든 최소 입력을 전달하고, 빌드 사용자는 그 복사본과 자신의 일회용 출력만 취급한다. 격리된 계정이라도 계정 내부에 다른 동시 작업이 공유 임시 파일을 두면 문제가 반복되므로 **빌드 전용 계정에는 한 번에 하나의 run**만 허용하고 이전 산출물/프로세스를 확인한 후 시작한다.

Xcode 자체의 `xcodebuild`/`xcrun`/`swbuild`가 전용 사용자의 실제 Darwin 임시 경로를 필요로 하는지 동일 Foundation probe와 제한 빌드로 재검사한다. 필요할 때 해당 경로에 대한 권한을 전용 사용자 경계 안에서만 최소 범위로 검토한다. Xcode 도구와 시뮬레이터 서비스에 필요한 추가 권한은 로그/파일 경로별로 좁혀야 한다. 계정 분리만으로 서비스·XPC·Mach 권한이나 OS sandbox 검증이 끝난 것으로 보지 않는다.

## 프로세스 수명(P5) 별도 충족 조건

현재 `start_new_session=True` + `killpg`는 최초 그룹만 제거한다. 실행한 코드가 `setsid`로 새 세션을 만들면 부모 그룹 정리를 벗어날 수 있다. 전용 UID는 권한 경계를 나누지만 **그 자체로 후손 종료를 보장하지 않는다**. 서비스 종료 시 해당 UID로 소유된 프로세스가 없음을 운영체제 수준에서 검증하고, 도중 새로 생성된 후손까지 포함한 원자적 종료 수단(예: 전체 전용 VM 폐기)을 설계해야 한다. 단순 `ps` 열거→kill은 경쟁 상태와 PID 재사용이 있으므로 완전한 수명 격리로 취급하지 않는다.

실행 프로세스 전체 수명 격리를 보장하는 구현·검사가 어려우면 Mac VM/별도 머신을 run 단위로 폐기하는 모델로 옮긴다. VM도 Xcode 설치·서명·Simulator 가용성, 네트워크, 실행 비용을 확인해야 한다. 검증되기 전에는 `execution.isolation_verified=false`를 유지하고 임의 비신뢰 제품 코드를 받아 자동 실행하지 않는다.

## 승격을 위한 검증 게이트

전용 사용자를 마련한 뒤 **그 사용자 세션 안에서** 사전 조건을 확인할 수 있도록
`scripts/check-isolated-ios-host --caller-uid <기존 UID> --caller-home <기존 HOME>`를 제공한다.
이 명령은 읽기 전용이며 실행자의 실효 UID, 시스템 계정 HOME, Darwin 임시 경로의
물리 위치·소유자·권한을 점검한다. 조건을 충족하지 않으면 exit2,
사전 점검만 통과하면 exit0을 반환한다. 어느 결과에서도 `isolation_verified=false`다.
계정을 만들거나 UID를 변경하지 않으며 Foundation/Xcode·후손 수명·원본 접근 차단은 검사하지 않는다.
기존 사용자 UID로 실행했을 때는 같은 UID/HOME이므로 거부되는 것이 정상이다.

원자적 쓰기 최소 재현은 `./scripts/probe-foundation-atomic /private/tmp/NEW-PROBE-DIR`로
실행한다. 미리 존재하지 않는 디렉터리여야 하며 도구가 작은 Objective-C/Foundation
프로그램을 해당 경로에 컴파일하고 합성 plist 두 개를 쓴다. stdout과 `result.json`에는 실행 모드, UID, 단계별 종료코드·로그 SHA-256,
probe 관찰값이 기록된다. 종료코드 0과 두 plist의 실제 합성 내용까지 확인해야 exit0이며,
컴파일·실행·내용 검증 실패는 exit2다. 기존 출력 경로(끊어진 symlink 포함)는 exit64로 거부한다.
`--sandbox NEW-PROBE-DIR`은 컴파일 후 바이너리를 실제 runner 프로필에서 실행하고
`sandbox.sb`와 그 digest를 보존한다. 컴파일은 sandbox 밖이며 전체 도구가 격리된 것은 아니다.
공유 Darwin T 디렉터리 쓰기는 허용하지 않는다. `probe.log`의 실행 전 sandbox 거부와
`non_atomic=true, atomic=false` 관찰을 구분한다. 출력 형식은 기존 두 boolean JSON에서
진단 결과 객체로 변경됐으며 원래 관찰값은 `probe_observation`에 있다.
일반 실행은 OS 기본 권한만 확인한다. **같은 바이너리를 실제 제품 제한 sandbox에서 실행한
결과**와 구분하여 기록해야 하며 이 도구가 격리 여부를 판정하지는 않는다.

1. **계정/파일 경계:** 호출 사용자 UID와 실행 UID가 다르고, 호출자 HOME·원본 checkout·비밀 canary 읽기/쓰기는 거부되며 고정 snapshot은 읽기만, run build/전용 tmp만 쓰기 가능해야 한다. 가능하면 실행 계정에서 Docker socket 및 외부 네트워크 거부를 확인한다.
2. **Foundation/Xcode:** 전용 UID에서 `atomically:YES` 저장·Xcode generic Simulator 빌드 exit0를 실제 재현한다. `xcrun_db`, `DerivedData/info.plist`, `swbuild.tmp.*`가 쓰인 물리 경로와 프로필 권한을 기록한다. stdout 성공 메시지만으로 판정하지 않는다.
3. **수명:** 정상 완료·timeout·강제종료 각 경우에 단순 자식과 `setsid` 분리 자식/손자가 살아남지 않음을 재현한다. 호스트 재부팅/서비스 crash 이후 유실 run 청소 절차도 확인한다.
4. **증거:** 실행 UID·환경 식별자, 프로필 digest, 단계별 로그/exit, 자원 정리 확인을 고정 subject/evidence와 연결하고 별도 reviewer가 재현한다. 기존 고정 run의 SHA를 새로운 성공 결과로 바꾸어 적지 않는다.

위 항목을 통과하지 못하면 ios-build 실패·미실행 check를 그대로 유지한다. acceptance 승인과 최종 PASS는 별도 절차다.

## P5 최소 재현 (2026-11-10)

관리자 권한 없이 `scripts/probe-process-lifetime --mode normal --sandbox NEW_DIR`와
`--mode timeout --sandbox OTHER_NEW_DIR`로 현재 runner의 그룹 정리 한계를 재현한다.
도구는 고정 합성 Python worker만 실행하며, 일반 자식과 `setsid` 자식의 heartbeat가
runner 반환 후에도 증가하는지 비교한다. PID 존재는 좀비·PID 재사용과 혼동되므로
생존 판정 근거로 사용하지 않는다. worker는 약 2초 뒤 스스로 끝나며 각 자식에
4초 alarm을 별도로 건다. 도구는 추가로 4.2초 대기하고 자체 만료 marker를 기록한다.
이 합성 worker의 자기 종료는 임의 제품 코드의 수명 격리나 실제 PID 정리 보장이 아니다.

`result.json`과 `worker.log`, sandbox 프로필/digest를 저장한다. 준비 완료 신호가
없거나 예상 정상/timeout 경로가 아니면 inconclusive(exit3), 탈출 관찰 또는 미관찰은
exit2다. 미관찰도 격리 PASS로 승격하지 않는다. 항상 isolation_verified=false,
cleanup_verified=false다. 기존 출력은 재사용하지 않는다. 새 서비스를 설치하거나
호스트 프로세스를 PID로 강제 종료하지 않는다. 강제 호스트 종료·재부팅은 미검사다.

현재 UID501의 실제 runner sandbox에서 정상 종료와 timeout 모두 일반 자식의 heartbeat는
멈추고 setsid 자식만 계속 증가했다. 두 분리 자식은 이후 자기 만료 marker를 남겼다.
따라서 `start_new_session`/`killpg`만으로 P5를 해결하지 못한다. 로컬
`man launchd.plist`의 AbandonProcessGroup 설명도 같은 process group 정리만 명시하므로
기본 launchd job 등록을 전체 후손 종료의 보장으로 제안하지 않는다.

## 전용 UID iOS 진단 실행기 (초기 구현)

`scripts/probe-dedicated-ios`는 기존 `scripts/runner`와 별개인 고정 입력 진단이다.
전용 UID에서 다음처럼 실행한다. 경로·SHA는 실제 준비한 고정 사본에 맞춘다.

```sh
scripts/probe-dedicated-ios --caller-uid 501 --caller-home /Users/dojoohwan \
  --original-app /Users/dojoohwan/workspace/godieor-app/README.md \
  --app /Users/Shared/NEW-STAGING/app --manifest /Users/Shared/NEW-STAGING/app-manifest.json \
  --out /Users/Shared/NEW-STAGING/incoming/NEW-RESULT
```

OS 계정의 UID/HOME 일치, caller HOME/기존 앱 파일의 실제 PermissionError,
getconf로 얻은 전용 UID의 물리 Darwin T 소유권/비공유 모드를 확인한다.
존재하지 않는 경로는 접근 거부 성공으로 취급하지 않는다. 입력 manifest/tree를 다시 대조하고,
링크·그룹/기타 쓰기·실행 UID가 수정 가능한 입력을 거부한다.
전용 HOME의 `.godieor-ios-probe.lock`에 비차단 flock을 유지하며 동일 도구의 동시 실행을 거부한다.
이 잠금은 협조적 진단끼리의 중복 방지이며 임의 동일 UID 코드나 이전 setsid 후손을 격리하지 않는다.

이후 별도 build 사본과 임시 HOME을 만들고, 기존 runner profile에 **확인한 전용 UID의 Darwin T와
그 별칭만** 읽기/쓰기 허용한다. 개발 UID의 공용 T나 전용 HOME/키체인 전체를 열지 않는다.
Xcode 버전→Foundation 컴파일/실제 plist 내용 검사→generic Simulator 빌드 순으로 실행한다.
중간 실패 시 다음 단계를 생략한다. profile·digest·단계별 argv/exit/로그 해시·입력 app SHA를 보존한다.
결과의 `ios_build_succeeded` 및 CLI exit0은 해당 진단 성공일 뿐이며 모든 결과에서
isolation_verified=false/cleanup_verified=false다. 기존 runner profile이나 acceptance verdict를 바꾸지 않는다.

P5는 계속 미해결이므로 현재 고정 제품의 진단에만 사용하고 임의 비신뢰 코드 자동 실행 서비스로
운영하지 않는다. XPC/Mach 접근 허용 등 기존 profile 한계, GUI/Xcode 서비스 초기화와 운영 비밀
차단 범위, 실제 후손 정리는 별도 검증 대상이다. 전용 계정에는 Apple ID/인증서를 넣지 않는다.
