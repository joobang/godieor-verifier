# VFY-03/04 · P5 후손 수명 실패 재현

- 요구사항 VFY-03/04, GD-010 draft. acceptance 승인 상태 변경 없음.
- 상태: 재현 도구·자체검사 완료 / 담당 codex-lifetime-08 해제. 독립 리뷰 대기.
- 시작 app 757f0eca6c9f1af870fcb6779e18aaffbe0eec1e,
  backend d277e3bb9f2e1b3a12a643f176e592529419d3e9,
  verifier ee0e282a43d0650b25e9c82c019a6dd18ccae839.
  모두 codex/vfy-foundation-diagnostics, clean.
- 작업 브랜치 세 저장소 codex/vfy-lifetime-probe, 단독 순차 수정.
- 환경 확인: UID501 이외 전용 사용자 없음, tart/prlctl/vfkit 없음,
  sudo -n -l 은 password required로 종료1. 관리자 인증을 요청/수집하지 않음.
- 범위: 환경 선택을 사용자에게 질의하고, 독립 진행 가능한 P5 합성 재현 도구 구현.
  정상 종료/timeout에서 일반 자식과 setsid 자식의 heartbeat를 비교한다.
  임의 명령 입력·계정 변경·서비스 설치·타 PID 강제종료 없음.
- 완료 조건: 실제 runner.command 경로의 생존 관찰과 한계를 로그/결과에 기록,
  합성 후손은 짧은 고정 시간 후 자가 종료, 신규 출력만 사용, 격리 승인 금지.
- 예상 실패: PID 존재만으로 실행 중이라고 오인, 셋업 지연을 cleanup 성공으로 오인,
  비정상 종료 시 테스트 후손 유출, launchd 기본 group 정리를 setsid 보장으로 오인.
- LEARN-0014 연결. ADR 새 선택 없음; runner-isolation 원본 적용.

## 실제 실행과 다음 행동

- `scripts/probe-process-lifetime --mode normal --sandbox /private/tmp/godieor-lifetime-normal-20261110`: exit2, runner 정상 반환 후 일반 heartbeat 3→3, setsid heartbeat 3→10.
- `scripts/probe-process-lifetime --mode timeout --sandbox /private/tmp/godieor-lifetime-timeout-20261110`: exit2, timeout 기록, 일반 32→32, setsid 32→40. 두 분리 자식 모두 자체 만료 marker 기록. 자동검사와 같은 PID를 의미하지 않는다.
- `scripts/self-test.sh`: exit0, 74개 성공. 실제 비제한 timeout 회귀 및 실행 전 실패의 inconclusive 처리·기존 symlink 출력 보존 추가.
- `man launchd.plist`: AbandonProcessGroup는 같은 process group만 정리한다고 명시. launchd 수명 격리 완료로 오인하지 않음.
- 사용자에게 전용 계정/VM 환경 선택을 질문했으나 사용자는 용어 설명을 요청했다. 설명 후 지금 선택할 필요 없다고 정정했다. 계정/VM 설치는 승인·확정된 선택으로 기록하지 않는다. OS 환경 변경 없음.
- 공통 status/handoff 및 LEARN-0014 갱신. 새 독립 리뷰/실제 전용 계정·VM/Xcode/강제종료·재부팅 검사는 미실행.
- app/backend 제품 코드·API 0.1.0-draft.2 및 기존 계약/migration digest 변경 없음. 새 integration evidence 없음. acceptance draft, isolation_verified=false, cleanup_verified=false, 통합 PASS 없음.
- 다음: 사용자에게 제품 기능 개발과 검증 실행 환경 구축의 차이를 설명한 상태. 실행 환경 선택은 미정이다. 별도 UID/VM 준비 없이 전체 격리 완료로 진행하지 않는다. 본 도구의 분리 컨텍스트 리뷰도 후속이며 현재 세션은 독립 reviewer가 아니다.
- 최종 커밋은 Git 이력 확인. 같은 커밋 안에 자기 SHA를 쓰지 않는다.
