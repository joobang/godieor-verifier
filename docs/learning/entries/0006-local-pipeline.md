# LEARN-0006 · 파이프라인을 가상 제공처부터 연결한 이유

종류: 초기 구현/예방 설계. 운영 장애 해결·성능 성과가 아니다. 사용자 이해/독립 검증 완료도 아니다.
근거: backend ADR-009, docs/reviews/2026-11-09-contract-review.md, docs/tasks/BE-01-local-pipeline.md.
고정 backend/계약/migration 참조는 docs/contracts/reference.json.

외부 API를 연결하기 전에 어댑터→정규화→안정 ID 매핑→원자적 publish→조회 경계를 구성했다.
가상 7건으로 네 분야/시즌/기기/미정의 표현과 로컬 API 구동까지 연결했다. 이는 실제 데이터 확보율 검증이 아니다.
공식 출처 조사에서 OTT의 플랫폼 가용성과 한국 시즌 최초 공개일이 서로 다른 정보임을 확인해, 근거 없는 날짜 생성 대신 보강 출처가 필요하다고 기록했다.

DB JSONB는 객체 키 순서를 보존하지 않아 단순 JSON.stringify 비교가 변경 이력을 과도하게 만들 수 있다.
canonical 비교 시 키를 정렬하는 예방 조치를 넣었다. 실제 장애 재현이나 반복 수집 테스트는 아직 하지 않았다.
팀도 이름보다 제공처 팀 ID를 매핑하고, 수집 실패는 마지막 성공 시각을 덮어쓰지 않게 구성했다.

실제 수행: 지원 런타임 버전 확인, 전용 DB 생성/초기 migration, Prisma introspection/generate, TypeScript build,
가상 수집 CLI, Nest 시작, 공개 API 응답 조회. 테스트 suite/독립 DB/권한 격리는 미실행.
스스로 설명할 질문: 왜 외부 수집 I/O를 DB publish 트랜잭션 밖에 두나? 무엇을 원자적으로 공개해야 하나? 플랫폼 목록이 공개일 근거가 아닌 이유는?
