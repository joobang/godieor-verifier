# VFY-03/04 · macOS iOS 빌드 실행 경계 설계 (미구현)

상태: 설계/운영 전제 검토. 요구사항 VFY-03/04, GD-001~010 초안. 승인된 격리 또는 제품 통합 PASS가 아니다.

## 관찰한 장애와 경계

2026-11-09 현재 실행기는 호출자 UID 501의 `sandbox-exec` 안에서 빌드한다. `TMPDIR`과 `HOME`을 각 run 아래로 돌려도 Foundation `atomically:YES`는 실제 Darwin 임시 경로 `/private/var/folders/.../T`를 사용했다. 그 물리 경로를 진단용 프로필에 허용하면 plist 원자적 저장이 성공하고 Xcode가 컴파일/링크까지 진입했지만 `swbuild.tmp.*` EPERM으로 exit65였다. 이는 개별 쓰기 실패에 대한 원인 분리이며 Xcode 전체의 성공이나 격리 증명이 아니다.

현재 UID의 공유 `T` 디렉터리를 정식 프로필에서 허용하면 같은 사용자의 다른 프로세스 임시 파일을 건드릴 수 있다. 해당 경로에 ACL만 추가하거나 `/var/folders` 별칭만 허용하는 변경은 보안 목표를 충족하지 못한다. `TMPDIR`만 지정하는 방식도 실제 실험으로 반증됐다.

## 선택할 실행 모델

후속 구현 후보는 **빌드 전용 표준 macOS 사용자 + 단일 run 실행 서비스**다. 이 사용자는 기존 개발 사용자와 UID/HOME/Darwin 임시 경로가 달라야 하고 운영 계정/키체인/소스 저장소/호스트 Docker socket/네트워크 자격 증명에 접근할 수 없어야 한다. 서비스가 고정 SHA에서 만든 최소 입력을 전달하고, 빌드 사용자는 그 복사본과 자신의 일회용 출력만 취급한다. 격리된 계정이라도 계정 내부에 다른 동시 작업이 공유 임시 파일을 두면 문제가 반복되므로 **빌드 전용 계정에는 한 번에 하나의 run**만 허용하고 이전 산출물/프로세스를 확인한 후 시작한다.

Xcode 자체의 `xcodebuild`/`xcrun`/`swbuild`가 전용 사용자의 실제 Darwin 임시 경로를 필요로 하는지 동일 Foundation probe와 제한 빌드로 재검사한다. 필요할 때 해당 경로에 대한 권한을 전용 사용자 경계 안에서만 최소 범위로 검토한다. Xcode 도구와 시뮬레이터 서비스에 필요한 추가 권한은 로그/파일 경로별로 좁혀야 한다. 계정 분리만으로 서비스·XPC·Mach 권한이나 OS sandbox 검증이 끝난 것으로 보지 않는다.

## 프로세스 수명(P5) 별도 충족 조건

현재 `start_new_session=True` + `killpg`는 최초 그룹만 제거한다. 실행한 코드가 `setsid`로 새 세션을 만들면 부모 그룹 정리를 벗어날 수 있다. 전용 UID는 권한 경계를 나누지만 **그 자체로 후손 종료를 보장하지 않는다**. 서비스 종료 시 해당 UID로 소유된 프로세스가 없음을 운영체제 수준에서 검증하고, 도중 새로 생성된 후손까지 포함한 원자적 종료 수단(예: 전체 전용 VM 폐기)을 설계해야 한다. 단순 `ps` 열거→kill은 경쟁 상태와 PID 재사용이 있으므로 완전한 수명 격리로 취급하지 않는다.

실행 프로세스 전체 수명 격리를 보장하는 구현·검사가 어려우면 Mac VM/별도 머신을 run 단위로 폐기하는 모델로 옮긴다. VM도 Xcode 설치·서명·Simulator 가용성, 네트워크, 실행 비용을 확인해야 한다. 검증되기 전에는 `execution.isolation_verified=false`를 유지하고 임의 비신뢰 제품 코드를 받아 자동 실행하지 않는다.

## 승격을 위한 검증 게이트

1. **계정/파일 경계:** 호출 사용자 UID와 실행 UID가 다르고, 호출자 HOME·원본 checkout·비밀 canary 읽기/쓰기는 거부되며 고정 snapshot은 읽기만, run build/전용 tmp만 쓰기 가능해야 한다. 가능하면 실행 계정에서 Docker socket 및 외부 네트워크 거부를 확인한다.
2. **Foundation/Xcode:** 전용 UID에서 `atomically:YES` 저장·Xcode generic Simulator 빌드 exit0를 실제 재현한다. `xcrun_db`, `DerivedData/info.plist`, `swbuild.tmp.*`가 쓰인 물리 경로와 프로필 권한을 기록한다. stdout 성공 메시지만으로 판정하지 않는다.
3. **수명:** 정상 완료·timeout·강제종료 각 경우에 단순 자식과 `setsid` 분리 자식/손자가 살아남지 않음을 재현한다. 호스트 재부팅/서비스 crash 이후 유실 run 청소 절차도 확인한다.
4. **증거:** 실행 UID·환경 식별자, 프로필 digest, 단계별 로그/exit, 자원 정리 확인을 고정 subject/evidence와 연결하고 별도 reviewer가 재현한다. 기존 고정 run의 SHA를 새로운 성공 결과로 바꾸어 적지 않는다.

위 항목을 통과하지 못하면 ios-build 실패·미실행 check를 그대로 유지한다. acceptance 승인과 최종 PASS는 별도 절차다.
