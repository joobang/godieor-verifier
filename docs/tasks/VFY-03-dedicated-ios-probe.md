# VFY-03/04 · 전용 UID 접근 경계와 제한 iOS 빌드

- requirement VFY-03/04, GD-010 draft. acceptance 승인 상태 변경 없음.
- 상태 진행, 담당 codex-dedicated-ios-11.
- 시작 app95be3b6/backend0ac4522/verifier794ea0d, codex/vfy-dedicated-account-plan, 모두 clean.
- 작업 브랜치 세 저장소 codex/vfy-dedicated-ios-probe. 단독 순차 수정, 별도 agent 없음.
- 범위: 전용 UID의 caller HOME 접근 거부·Darwin T 소유권 확인 후 단일 run 잠금을 잡고
  해당 UID의 T에만 읽기/쓰기 허용한 별도 진단 profile로 Foundation 및 generic Simulator 빌드 실행.
  고정 입력 manifest를 검증하고 build 사본만 실행. 일반 runner profile은 변경하지 않음.
- 완료: 실제 ACL 재검사·Foundation·Xcode 결과와 profile/로그 해시 보존. 성공을 전체 격리/제품 PASS로 해석 금지.
- 예상 실패: 잘못된 caller UID/HOME으로 공유 temp 허용, ACL 적용 후에도 원본 접근,
  같은 UID 동시 run, 변조된 snapshot, Xcode XPC/캐시 추가 거부, timeout 후 setsid 후손 생존.
- P5 미해결이므로 고정된 현재 제품 코드 진단만 수행하며 임의 입력 자동 실행 서비스로 승격하지 않음.
- LEARN-0014, 원본 설계 docs/runner-isolation.md. 새 정책/인증서·Apple ID·운영 DB 변경 없음.

## 구현 checkpoint

- `scripts/probe-dedicated-ios`, dedicated_ios.py, test_dedicated_ios.py 추가.
- `scripts/self-test.sh`: 81개 성공. 원본 읽기 가능/경로 부재/same UID/변조 입력/링크/잠금 경쟁/컴파일 실패 후 제품 미실행 경로 검사.
- 실제 UID502 실행을 위해 고정 verifier commit을 먼저 만들고 별도 shared staging을 준비한다.
- 결과는 별도 진단 기록이며 전체 integration evidence를 생성하거나 독립 승인하지 않는다.

## 실행 준비·인증 대기

- 코드 checkpoint 9cbeb19, frozen build root 수정 8b85f18. 최종 81개 자체검사 exit0.
- 입력 staging /Users/Shared/godieor-ios-check-143ffcc4:
  app95be3b6, verifier-v2 8b85f18 고정 snapshot·manifest. 최초 verifier 사본9cbeb19는 실행에 사용하지 않는다.
- staging 입력은 freeze, incoming은 godieorbuild 명시 ACL과 결과의 개발 사용자 읽기 상속 ACL만 추가.
  개인 HOME 원본 접근 차단 ACL은 이전 작업 상태 그대로 유지.
- 비공개 입력 도구로 테스트 계정 인증 대기. 아직 UID502 검사/프로필 확장/실제 Xcode 빌드 미실행.
- 코드 자체검사와 실제 실행을 구분한다. 별도 컨텍스트 리뷰·통합run·P5 해결 없음.
- 다음은 인증 후 run-account-check.sh 실행. 새 run 디렉터리만 사용하며 기존 로그를 덮어쓰지 않는다.
