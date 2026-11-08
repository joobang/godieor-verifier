# 참고 자료에서 채택한 것과 제외한 것

작성일: 2026-11-06 KST. 현재 상태: bootstrap 설계. 전체 자동화 구현 완료를 뜻하지 않는다.

## 읽은 범위

- [wd-harness README](https://github.com/joobang/wd-harness/blob/main/README.md), workflow.json,
  reviewer/tester, curiosity/test/review 프롬프트, DEVELOPMENT/TEST 문서.
  [읽은 파일과 blob SHA](reference-files.json). main에서 선별 조회했으며 전체 저장소·공통 commit 감사를 수행하지 않았다.
- 김민태, [AI와 개발한 1년 — 사라진 건 없고, 달라진 건 많다](https://medium.com/@ibare/one-year-with-coding-agents-e1cd0e3e2dbd).

글에서 참고한 핵심은 구현과 다른 문맥의 설계 검토, 검사와 AI 판단의 분리,
지적 이력을 통한 재검토, 실행 결과를 규칙·설계 개선과 개인 학습으로 연결하는 흐름이다.
글의 사례 규모나 저자가 만든 도구 자체를 GODIEOR의 필요 조건으로 보지 않는다.

## GODIEOR에 적용

| 참고 | 채택 | 반영 위치/상태 |
|---|---|---|
| wd-harness: 명세·계획·실행 산출물 | requirement ID → 기대값 → 실행 근거 연결 | acceptance 초안, evidence 계약 |
| wd-harness: curiosity 점검 | 가정·실패 모드·경계 조건 질문 | 작업 템플릿. 개수 할당 없이 실제 위험만 작성 |
| wd-harness: 테스트 실행 수단 확인 | 빌드·API·저장 재조회·iOS 사용자 흐름 구분 | 필수 check ID. 외부 runner는 다음 구현 |
| wd-harness: 결과 기록 | 명령·종료 코드·실행/미실행 분리 | 판정 엔진. AI 문장으로 실행 검사를 대체하지 않음 |
| 독립 검토 원칙 | 구현 history 없는 설계/코드 리뷰 | 리뷰 프롬프트. OS 격리는 별도 미완료 |
| 재검토 이력 원칙 | finding ID를 유지하며 해결 근거 추적 | reviews/ledger.json + 수동 절차, 자동화는 미구현 |
| 피드백 원칙 | 반복 실패에서 규칙 신설/개정/폐지 제안 | prompts/rule-audit.md, 사람 승인 필요 |
| 학습 기록 원칙 | 결정·문제·기술 해설을 근거와 연결 | verifier docs/learning에 통합. 각 레포의 원본 ADR/run 연결; 별도 지식 서비스 없음 |

## 현재 제외

- 9단계 고정 상태 머신·hook·플러그인 생태계: 작은 변경에도 산출물/설정 비용이 커진다.
- Sonnet/Opus 등 단계별 모델 고정: 모델/비용 정책이 미정이며 역할 분리가 먼저다.
- 전문가 인물 역할극·주관적 품질 점수·`APPROVED` 문구 gate: 검증 증거를 대신하지 못한다.
- 질문·심각한 지적의 최소 개수 강제: 없는 문제를 만들고 검토 비용을 키울 수 있다.
- 리뷰 에이전트가 제품 코드를 고치는 흐름: 발견과 수정 책임을 분리한다.
- 매번 모든 검사 유형 강제: 승인된 필수 검사와 변경 위험에 맞게 실행 범위를 정한다.
- 관측 대시보드·코드 생존율 추적·규칙 수백 개의 전면 감사: 실제 실패 이력이 쌓인 뒤 필요성을 판단한다.
- 자동 수정 무한 루프·자동 merge/배포: V1에서는 사람 결정으로 마친다.

검증이 실패하면 먼저 제품 결함·검사 결함·환경 문제·정책 미정을 구분한다.
검사 기준 변경이 필요하면 변경 제안과 근거를 남기고 다시 승인받는다.
