# VFY-03 · 전용 macOS 빌드 계정 선택

- 요구사항 VFY-03/04, GD-010 draft. 승인 기준 변경 없음.
- 상태: 실행 방식 확정·절차 준비 완료, 계정 생성/실환경 검사 대기. 담당 codex-account-09 해제.
- 시작 HEAD: app 0daddf0, backend 308d7b3, verifier 4255c94.
  모두 codex/vfy-lifetime-probe, clean. 작업 브랜치 codex/vfy-dedicated-account-plan.
- 사용자 확정(2026-11-10): “전용 계정 … 이렇게 가자”. 전용 macOS 계정 방식 채택.
- 범위: 정책 P10/아키텍처/계획 반영 및 생성·검사 절차. 제품 코드 변경 없음.
- 예상 실패: 전용 계정에 Apple ID/인증서/개인 HOME 접근 권한 전달,
  계정 분리만으로 P5·격리 완료 오인, 전용 계정에서 개인 checkout 접근 실패.
- 완료: 개인 iPhone 설치는 기존 개발 계정, 자동검증은 전용 표준 계정으로 역할 분리.
- 실제 확인: sysadminctl -h의 계정 생성/비밀번호 대화식 입력 방식 확인.
  dscl에서 godieorbuild 계정 부재 확인. 현재 앱 빌드는 simulator·서명 비활성화.
- OS 계정 생성/로그인/키체인 변경/실기기 설치/Xcode 실행은 미실행.
  생성에는 관리자 인증과 새 계정 비밀번호 설정이 필요하다. 비밀번호를 대화/소스에 기록하지 않는다.
- LEARN-0014: 전용 UID 선택은 사용자 확정이나 실제 안전성 검증/P5 해결과 별개.
- ADR: runner-isolation 기존 설계를 사용자 선택으로 갱신; 별도 기술 대안 추가 없음.
- 절차: docs/dedicated-account-setup.md. 다음 계정 준비 후 사전점검/입력 전달/제한 probe→Xcode→수명 게이트.
- 공통 문서 동기화·diff --check·export-context --check로 문서 검증. 실행 코드 변경 없어 자기검사 재실행 없음.
- 독립 리뷰·통합 evidence 없음, acceptance draft 및 isolation_verified=false 유지.
