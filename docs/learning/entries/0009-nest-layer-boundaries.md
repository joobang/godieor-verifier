# LEARN-0009 · Nest를 사용한 것과 책임을 분리한 것은 다르다

종류: 실제 개발 구조 결함과 수정. 운영 장애·성능 개선 수치는 아니다. 2026-11-09 KST.
상태: 작성자 실행 확인, 별도 고정 코드 리뷰에서 추가 지적 없음 보고. 승인 acceptance의 iOS 통합 검증 전.

원본: backend [ADR-011](../../../../godieor-backend/docs/decisions/011-nest-feature-layering.md),
[BE-03](../../../../godieor-backend/docs/tasks/BE-03-nest-layering.md), [서버 구조](../../../../godieor-backend/docs/backend-architecture.md).
코드 고정 SHA는 3863f027596f787d1c5939c7af74eca7fa0eb480이며 최종 문서 커밋은 Git 이력을 참고한다.

사용자가 Controller→Service→Repository 구조가 없다고 지적했다.
실제 module.ts에는 여러 HTTP Controller와 오류 필터가 있었고 Catalog/Pipeline에는 입력 검증·표현·쿼리·트랜잭션·스케줄이 섞여 있었다.
이를 bootstrap이라는 이유로 방치하면 확장/교체/단위 검사 경계가 불분명해진다.

기능별 모듈을 조립하고 Controller는 HTTP/pipe, Service는 처리 흐름, Repository는 영속 IO를 담당하게 했다.
후보 CLI도 별도 Nest 모듈을 부팅해 DB 없이 Repository/Client를 주입받는다.
미구현 auth/users는 빈 repository를 만들어 완성된 것처럼 보이지 않고 기존 차단을 유지한다.

확인: 빌드/28개 자체 검사, 별도 tmpfs DB migration·7건 저장·반복 ID 유지·연기/실패 보존,
전후 21개 API 응답과 양방향 커서 호환 비교. 계층 검사 AST가 adapter.fetch 위임까지 직접 IO로 오인해 검사식을 고쳤다.
이는 개발 검사 오류이며 제품 장애로 표현하지 않는다. iOS 통합/승인 PASS는 없다.

질문: 왜 서비스에서 Prisma를 바로 호출하지 않았는가? 읽기 snapshot과 scope publish 트랜잭션은 어느 레이어가 지켜야 하는가?
파일만 나눠 놓고 기존 혼합 클래스를 호출하면 어떤 문제가 남는가?
관련 코드/계약/구조가 바뀌면 원본·이 기록의 주장을 재검토한다. 사용자 이해도나 면접 설명 완료는 기록하지 않았다.


독립 코드 리뷰 범위/한계는 [BE-03 리뷰](../../../reviews/2026-11-09-nest-layering.md)를 참조한다.
reviewer의 대역 비교와 작성자의 실제 임시 DB 실행은 각각의 근거로 보존했다. 새로운 커밋/변경에는 그대로 재사용하지 않는다.
