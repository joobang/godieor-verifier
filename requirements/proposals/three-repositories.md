# 세 저장소 acceptance 확장 제안

상태: **제안 / 미승인**, 2026-11-09. 실제 `acceptance.yaml`·기대값·필수 검사 목록은 이번 문서 동기화로 바꾸지 않았다.
구현 결과가 아니라 제품 정책과 API 계약에서 기대값을 도출해야 한다.

| 기존 ID | 새 책임/관찰점 제안 | 승인 전 남은 정책 |
|---|---|---|
| GD-001 | app 달력/카드 + backend 날짜 범위·정렬 API + 통합 집합 비교 | P04, P07, P09 |
| GD-002 | backend 필터 의미 + app 요청/선택 + 통합 포함/제외 | P05, P06, P09 |
| GD-003 | app 설정 저장·재조회, 계정 추가 시 backend 동기화 별도 기준 | P03 |
| GD-004 | backend 상세 계약과 출처 + app 원본 정밀도 표시 | P04, P05, P09 |
| GD-005~006 | backend 정규화·DB 중복 방지·변경 후 안정 ID + API 관찰 | P05, P06 |
| GD-007 | backend 시간 의미/범위 API + app 시간대 표시 + 통합 기대값 | P04 |
| GD-008 | backend 재수집·지연·연기/취소 + app 최신성/장애 표시 | P08, P09 |
| GD-009 | 네 제공처 adapter의 실제 접근/범위 확인 + 독립 fixture 계약 검사 | P05, P06, P08, P12 |
| GD-010 | iOS 빌드 + backend 실행·임시 DB migration + 비밀/권한 경계 | P01, P02, P10 |

별도 시스템 기준 ID를 검토할 항목: 두 SHA/계약/마이그레이션 binding,
검증 범위 식별(app-only/backend-only/integration), 필수 검사 누락 차단,
실행 권한 경계와 실제 실행 진위. ID와 기대값은 검토 후 새 acceptance 버전에서 확정한다.

승인 단계: 정책 답변 → 원자적 기대값/독립 예제 → 검사 matrix → 독립 검토 → 사용자 승인 → 새 버전.
이 제안의 표만으로 검증 가능한 acceptance가 완성됐다고 보지 않는다.
