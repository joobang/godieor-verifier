# VFY-03 · Foundation 제한 실행 진단 자동화

- requirement: VFY-03/04, GD-001~010 draft. acceptance 승인 상태 변경 없음.
- 상태: 도구 구현·자체 검사 완료, 독립 리뷰 대기. 담당 codex-foundation-07 해제.
- 시작: app 7c868d9604d4b0e6b4e175f449c0966fb4f169df / dev,
  backend 2a9d06f01b6c1a1b1080db4b33ae32de386e287f / dev,
  verifier 1081d93dff25159a3e848d63c99485300a453b9d / codex/vfy-foundation-probe-hardening. 모두 clean.
- 작업 branch: 세 저장소 codex/vfy-foundation-diagnostics, 순차 단독 수정. 별도 agent 없음.
- 범위: 기존 Foundation 도구에 실제 runner 프로필 제한 실행·로그/결과 기록을 추가.
  공통 상태 문서의 누락된 최신 후속을 갱신한다. 제품 코드/계약/기준/계정 변경 없음.
- 완료: 일반/제한 실행을 명시적으로 구분하고 compile 오류, sandbox 시작 오류,
  원자적 저장 실패를 성공과 혼동하지 않으며 기존 출력은 덮어쓰지 않는다.
- 예상 실패: 상대 출력 경로로 바이너리 실행 실패, 기존/심볼릭 링크 출력 재사용,
  sandbox 시작 거부를 Foundation 실패로 오인, 공용 Darwin T 권한의 우발적 허용.
- 학습: LEARN-0014. ADR: 기존 runner-isolation 설계 적용, 새 기술 선택 없음.
- 독립 검증: 이번 세션은 도구 구현 담당. 독립 승인/제품 통합 PASS를 작성하지 않는다.

## 실제 실행과 인계

- `scripts/self-test.sh`: 최종 exit0, 71개 성공. 최초 1개 검사는 macOS 기본 임시 경로 안의 run 하위 경로까지 금지하는 과도한 assertion이어서, 공유 상위 경로 grant 금지로 고친 뒤 재실행했다.
- `scripts/probe-foundation-atomic /private/tmp/godieor-foundation-20261110-normal`: exit0, 두 plist 내용 확인.
- `scripts/probe-foundation-atomic work/foundation-relative-check` (app cwd): exit0, 상대 경로 재현 성공.
- `scripts/probe-foundation-atomic --sandbox /private/tmp/godieor-foundation-20261110-sandbox-final`: exit2, 컴파일 exit0, 제한 probe exit2, non_atomic=true / atomic=false. result.json과 로그·프로필 digest 보존. sandbox 실행 전 거부가 아닌 실제 저장 실패다.
- 기존 출력/끊어진 symlink 거부, 컴파일 실패 시 실행 생략, 실행 실패/timeout의 성공 차단은 합성 회귀 검사다.
- `git diff --check`: 종료 전 확인. 최종 SHA는 Git 이력 참조. 공통 status/handoff 사본 동기화.
- API 0.1.0-draft.2, 계약 manifest 8dfc69a8c6a5f9feb91f2d0cf6d661eec16a1aacb8e980b7abe880cd0b1f3b1e, migration 29ef8ef0d520f44b6a633e8f017144a3e2b2199189461a88ba99bc296c42f5b9 유지.
- app/backend 제품 코드는 변경하지 않음. 새로운 integration evidence/독립 리뷰/전용 계정 생성/Xcode 재빌드/P5 검사는 수행하지 않았다. acceptance draft, isolation_verified=false, 통합 PASS 없음.
- 다음: 전용 실행 UID 또는 run별 VM 준비 후 같은 제한 probe→Xcode→후손 수명 게이트 실행. 도구 변경의 분리 컨텍스트 리뷰도 필요하다. 현재 세션을 독립 reviewer로 간주하지 않는다.
