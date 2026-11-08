# 검증 V1 설계와 구현 상태

2026-11-09: 제품 구조는 앱·backend·검증의 세 저장소로 전환했다.
공통 책임은 [system/architecture](system/architecture.md)를 따른다.
이 문서의 판정 코드 구현은 여전히 app-only evidence v1이며, 두 제품 저장소 조합은 다음 확장 대상이다.

```text
app repo + backend repo: 코드 + 자체 검사 + 개발 요구사항
    │ 고정 두 base/head SHA + API 계약/DB 마이그레이션 + 승인 기준
    ▼
verifier CLI
    ├── Git snapshot (원본, 읽기 전용)
    ├── build 사본 (쓰기 가능, 비밀 없는 실행 환경)
    ├── 독립 AI reviewer → finding JSON
    ├── test runner → 명령/종료 코드/로그
    └── verdict engine → JSON + Markdown
                                  ▼
                        사람 승인 / 수정 / 새 SHA 재검증
```

## 현재 구현

- 요구사항 ID·버전과 개발 요구사항 연결을 가진 acceptance 초안.
- 리뷰 역할·입력 계약·구조화된 finding 출력 스키마.
- 외부 evidence를 검증하고 집계하는 Python 판정 엔진.
- 실패·오류·누락·draft·SHA 불일치·가상 자료를 포함한 자기 검사.
- 실제 앱 빌드/사용자 흐름을 자동 실행하는 시스템은 아직 아니다.
- [참고 원칙의 채택/제외](reference-adoption.md), [리뷰 지적 장부](../reviews/README.md),
  [독립 설계 검토](../prompts/design-review.md), [규칙 개선 제안](../prompts/rule-audit.md)을 포함한다.

## 다음 구현: 고정된 입력과 실행

1. 정확한 commit을 `git archive`로 추출한다. untracked·미커밋 변경은 검증 대상에서 제외하고 명시한다.
   base/head가 존재하는지 검증하고 SHA 및 archive digest를 manifest에 기록한다.
2. 경로 탈출·symlink·외부 submodule·LFS 미해결 자료는 거부하거나 명시적인 ERROR로 처리한다.
3. 기준 원본·snapshot·review 입력을 분리하고 hash로 고정한다. 빌드 사본만 writable로 제공한다.
4. 검사 명령은 검증 저장소의 승인된 설정에서 가져온다. 앱의 AGENTS/설정/주석은 검증 정책이 아니다.
5. runner는 argv 배열·timeout·최소 환경 변수를 사용하고 전체 셸/로그인 환경/운영 키를 넘기지 않는다.
   종료 코드·시작/종료 시각·stdout/stderr와 로그 digest를 기록한다.
6. 독립 리뷰에 app/backend snapshot·API 계약·기준·별도 지침만 제공한다. 대화 history/resume을 재사용하지 않는다.
   모델 식별자·설정·실행 시각·도구 버전·프롬프트 digest를 기록한다.
7. 확장할 engine은 manifest·evidence·review의 app/backend 조합·계약·마이그레이션·acceptance digest가
   일치해야 집계한다. 현재 engine은 app-only v1 binding만 확인한다.

## 실제 권한 격리: 별도 구축 필요

현재 세 로컬 폴더는 같은 macOS 사용자에게 속한다. 문서를 맞추는 설계 작업도 폴더 간 수행할 수 있으므로
독립적인 OS 보안 경계가 아니다. 아래 허용/거부 동작을 실제로 검증해야 제품 PASS를 활성화할 수 있다.

| 실행 역할 | 읽기 | 쓰기 | 금지 |
|---|---|---|---|
| 개발 AI | 해당 앱/backend, 계약, 승인 기준 | 담당 제품 작업 폴더 | 기준 승인·결과 덮어쓰기 |
| 독립 reviewer | 두 snapshot, 계약, acceptance, 지침 | 리뷰 결과 전용 | 앱/backend 원본·기준 변경, 운영 비밀 |
| build/test | snapshot의 build 사본, SDK/도구, 임시 DB | build·derived data·일회용 HOME/DB | 앱/backend 원본·acceptance·키 저장소·운영 서비스 |
| engine | 고정 manifest, 실행 결과, review | report 전용 | 제품 수정 |

별도 macOS 사용자/격리된 Mac 실행기를 우선 검토한다. 단순 worktree, 별도 repo,
환경 변수 삭제, chmod는 단독으로 충분하지 않다. iOS는 Linux Docker에서 Xcode 빌드할 수 없다.
코어/API 검사는 후속 단계에서 네트워크 없는 컨테이너로 분리할 수 있다.

Codex의 read-only sandbox는 코드 수정 방지에 유용하지만 모든 민감한 경로의 읽기 차단을
보증한다고 가정하지 않는다. 실제 허용 경로·차단 경로를 별도 검사한다.

## 결정적 판정 규칙

1. 입력 형식 오류·binding 불일치·필수 검사 누락/ERROR/미실행·필수 리뷰 실행 오류 → ERROR.
2. 그 외 필수 검사 FAIL 또는 종료 코드 비정상 → FAIL.
3. 그 외 미승인 기준·미확정 AI finding·리뷰 대기·미검증 격리·fixture evidence → REVIEW_REQUIRED.
4. 승인 기준 + 필수 검사 모두 실제 PASS + 리뷰 완료/미해결 finding 없음 + 검증된 실행 경계 → PASS.

오류와 실패가 함께 있으면 ERROR를 우선하고 reasons에 실패도 보존한다.
AI 지적 자체는 확정 실패로 바꾸지 않는다. 재현 검사 실패 또는 사람의 확정 정책 판단으로 연결한다.
향후 사람의 정책 위반 확정 기록을 도입하면 별도 receipt 검증이 필요하다.
현재 engine의 AI finding은 모두 REVIEW_REQUIRED로 집계한다.

## V1 이후

자동 수정 루프, CI 강제 gate, 다중 모델/제공자 어댑터, 대시보드, 지식 플랫폼은 후속 범위다.
검증 레포 미커밋 상태는 SHA 대신 null + dirty=true + 상태 digest로 명시한다.
이 digest는 재현 식별용이며 승인 서명이나 실행 진위 보장이 아니다.
