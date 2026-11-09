# LEARN-0014 · 고정 소스와 실제 실행의 경계

작성자 기술 해설 초안. 원본 docs/tasks/VFY-03-04-runner.md, 사용법 docs/runner.md. 통합PASS/학습 성과/성능 개선을 주장하지 않는다.

SHA 문자열만 지정해도 Git replace ref나 로컬 export속성이 추출 결과를 바꿀 수 있었다. 독립 리뷰에서 가상marker/임시repo로 재현했다. raw tree/blob 읽기, replace금지로 바꾸고 로컬속성을 적용하지 않는다. fsmonitor가 status 단계에 호스트 프로그램을 실행하거나, promisor의 missingobject 조회가 remote helper를 실행하는 문제도 재현돼 Git 환경·설정·모든transport를 차단했다. 경로는 Unicode와 대소문자충돌을 선제거부한다.

읽기 전용snapshot은 빌드사본과 분리한다. chmod는 동일사용자 OS격리가 아니다. 최소HOME·제한sandbox에서 가상canary/원본 접근·snapshot읽기/쓰기·build쓰기를 실험했고 제한된허용/거부만 확인했다. 이결과를 isolation_verified=true로 확장하지 않는다. setsid후손은 최초processgroup을 벗어나므로 전체수명정리는 여전히 미해결이다.

실행기는 digest고정PostgreSQL 이미지를 기존DB와 다른 tmpfs/동적loopback포트로 실행하고 고유컨테이너명으로 정리한다. run응답timeout도 생성시도부터 cleanup을 시도하도록 수정했다. 이timeout경로는 mock회귀검사이며 실제Docker 장애주입은 아니다.

실제 제한실행에서 backend47개검사와 새DBmigration/반복수집ID/달력·상세smoke를 수행했다. iOS 제한빌드는 임시쓰기 경계문제를 드러냈고 당시실행을 실패로 기록했다. 원본환경에서 과거빌드가 성공했다는 사실로 이실행의 실패를 덮어쓰지 않는다. 실행한단계와 전체GD승인검사는 별개이므로 부족한필수검사는 SKIPPED→ERROR로 남긴다. 관련Git·실행정책·런타임이 바뀌면 이주장을 재검토한다.

후속 재현(2026-11-09): Foundation `NSDictionary writeToFile:atomically:NO` 및 일반 `NSData writeToURL`은 제한된 build HOME에 정상 저장됐지만, `atomically:YES`와 `NSDictionary writeToURL:error:`는 동일 경로에서 EPERM이었다. macOS 사용자 임시 폴더의 물리 경로 `/private/var/folders/.../T`를 별도로 허용하면 두 atomic 쓰기가 성공했고, `C`만 허용하면 실패했다. 이는 기존 `/var/folders` 별칭만 허용한 시도와 달리 실제 물리 경로를 비교한 결과다. Xcode도 `DerivedData` 초기 오류 없이 빌드 단계로 진입했지만 `swbuild.tmp.*` 및 링커 문제로 exit65였다. 사용자 공용 T 폴더 전체를 허용하면 격리 목표가 약화되므로 코드에 반영하지 않았다. 외부의 지정된 실행 사용자 환경은 후속 설계 과제이며 아직 안전성을 입증하지 않았다.

후속 설계(코드/환경 미적용): `docs/runner-isolation.md`에 전용 실행 UID의 비밀·Darwin 임시 디렉터리 경계, run 단독 실행, 서비스 종료·VM 폐기에 따른 `setsid` 후손 수명 검증 조건을 적었다. 전용 사용자 격리는 파일 접근 면을 줄이는 제안이며 프로세스 트리 전체 종료의 증거는 아니다. 가상 probe/실제 Xcode 재실행·후손 장애 주입은 추후 별도 기록한다.

추가 사전점검 구현: `scripts/check-isolated-ios-host`가 OS 계정 기준 UID/HOME 및 Darwin T의 물리 경로·소유·접근 모드를 확인한다. 실제 사용자 UID 501에서는 `same_uid_as_caller`/`home_overlaps_caller_home`로 거부됐으며 전용 사용자 합격 사례는 아직 없다. 모의 조건 4개 검사는 자기검사이고 실제 OS 격리 검증이 아니다. 결과는 항상 `isolation_verified=false`로 고정한다.

동일 원인에 대한 재현성 보강: Objective-C/Foundation 합성 plist probe를 저장소에 추가했다. 같은 Mac UID 501의 일반 실행에서 비원자적/원자적 쓰기가 모두 성공했으며, Codex의 기존 sandbox 안에 runner `sandbox-exec`을 중첩했을 때는 `sandbox_apply: Operation not permitted`(71)로 프로그램 실행 전에 거부됐다. 이 두 결과는 과거 제한 실행에서 관찰한 atomic EPERM을 반증하지 않는다. 별도 실행 ID의 제한된 환경에서 다시 비교해야 한다.

2026-11-10 후속: Foundation 비교 실행을 도구화해 실제 runner 프로필·digest·단계별 로그와 종료코드를 보존하고, 성공한 프로세스의 실제 plist 내용도 확인한다. 현재 UID 501에서 일반 실행은 두 저장 모두 성공했고, 제한 프로필은 실행 자체가 시작돼 `non_atomic=true, atomic=false`/exit2를 재현했다. 과거 중첩 sandbox exit71과 달리 이번에는 Foundation 저장 실패를 관찰했다. 사용자 공유 Darwin T 권한은 추가하지 않았다. 전용 UID/Xcode/후손 수명 검증은 여전히 미실행이며 이 결과는 독립 승인 evidence가 아니다.

2026-11-10 P5 실제 재현: 고정 합성 후손의 heartbeat 증가를 runner 반환 뒤 비교했다. 실제 제한 프로필의 정상 종료와 timeout 모두 일반 자식은 정지했지만 setsid 자식은 계속 파일을 갱신했다. 각 합성 자식은 자체 2초 기한과 4초 alarm을 가지므로 재현은 짧게 끝난다. 이는 제품 코드 전체 정리 구현이 아니라 기존 한계의 관찰이다. PID 존재나 `.done` marker를 OS 수명 격리 증거로 사용하지 않았다. 전용 UID/VM 선택은 아직 사용자 확정이 없으며 계정/가상화 도구를 설치하지 않았다.

2026-11-10 사용자 후속 선택: 전용 macOS 표준 계정 방식을 채택했다. 개인 iPhone 서명·설치는 기존 개발 계정에서 수행하고 검증 계정에 인증서를 전달하지 않는다. 앞 절의 선택 미정은 당시 기록이다. 계정 생성/실환경 성공/P5 해결은 아직 없다.
