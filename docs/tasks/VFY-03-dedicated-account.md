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

## 실제 계정 준비 재개 · 2026-11-10

- 담당 codex-account-10, 진행. 시작 app39cd67a/backend11be74b/verifierab8fb90, 기존 작업 브랜치 codex/vfy-dedicated-account-plan, 모두 clean.
- 사용자 “좋아 다음 작업 시작해봐”에 따라 기존 전용 계정 선택의 실제 생성 단계 진행.
- 범위: macOS 시스템 설정에서 표준 계정 생성 준비, 관리자 인증/새 비밀번호 입력은 사용자 직접 수행, 생성 후 UID/권한 확인. 개인 Apple ID/키체인/인증서 변경 없음.
- 예상 실패: 관리자 인증 대기, 표준 대신 관리자 선택, 개인 HOME 접근권한 확대, 생성 전후 상태 오인.
- 요구사항/LEARN/기준은 위와 동일. 생성·로그인 확인 전 완료로 기록하지 않는다.

### 계정 생성 확인 · codex-account-10

- 사용자가 macOS 관리자 인증 및 새 계정 비밀번호 입력·사용자 생성을 직접 완료했다.
- 시스템 설정 UI에서 GODIEOR Build / 표준 사용자 표시 확인.
- `id godieorbuild`, `dscl . -read /Users/godieorbuild UniqueID PrimaryGroupID NFSHomeDirectory UserShell`:
  UID502, GID20(staff), HOME /Users/godieorbuild, shell /bin/zsh.
- `dseditgroup -o checkmember -m godieorbuild admin`: 관리자 그룹 비회원.
- HOME 모드750 및 everyone deny delete ACL 관찰. UID 분리만으로 개인 HOME 접근 차단이 보장되지 않으며, 기존 사용자 HOME도 staff 그룹으로 접근 가능할 수 있어 실제 계정 실행에서 확인해야 한다.
- `sudo -n -u godieorbuild /usr/bin/id`: 암호 필요로 exit1, 전환 미실행.
- 비공개 입력 도구로 테스트 계정 암호 요청 중. 관리자/Apple ID 암호는 요청하지 않았다. 인증 전 실행 성공으로 기록하지 않는다.
- 고정 입력 staging: /Users/Shared/godieor-account-check-4b8fe0c2.
  app39cd67a/verifierab8fb90 고정 snapshot과 manifest, 진단 실행 shell 준비.
  입력은 개발 사용자 소유·다른 사용자 쓰기 금지, incoming은 700+godieorbuild의 명시적 생성 ACL만 추가.
  개인 HOME/원본 checkout 권한은 변경하지 않았다.
- 현재 미실행: UID502 내 사전점검·파일 경계·Foundation/Xcode 검사. P5 open/격리 미검증/통합 PASS 없음.
