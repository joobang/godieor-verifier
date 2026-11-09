# LEARN-0011 · 공식 공지 근거와 제품 이벤트 식별자를 분리하기

2026-11-09, 실제 개발 선택과 예방 설계·작성자 실행 기록. 운영 장애/성과 수치·사용자 이해도는 기록하지 않는다.

공지URL은 출처 근거이고 작품/공개 사건 식별자가 아니다. 제목·날짜·시즌에서 키를 만들면 날짜 정정 때 새 이벤트가 생기거나 같은 제목이 섞일 수 있다. 이를 예방하기 위해 수동 고정 contentKey/eventKey와 현재 검토 revision을 별도로 입력한다. backend ADR-013 / DATA-02B / docs/reviewed-publish.md가 원본이다.

기존 CollectionService/Repository의 provider key 매핑·scope 트랜잭션을 재사용했다. 후보 writer lock은 검토 파일 변경을 막고 provider advisory lock 안의 Client identity 비교는 기존 국가/플랫폼/작품/알려진 시즌 덮어쓰기를 거부한다. 미정 시즌에 번호를 보완할 수 있지만 다음 시즌은 새 eventKey가 필요하다. 시간대가 없으면 날짜만 보존하며 게시일을 sourceUpdatedAt으로 만들지 않는다.

작성자 실행: 전체47개 자체 검사, 일회용 PostgreSQL에서 반복 ID·날짜 정정·미정→확정 시즌·변경 거부·stale/불완전 입력 보존 확인. 공식 공지4건을 로컬DB로 수동 반영하고 재실행 후4건/최초변경이력4 유지, 기존 fixture7건 보존. 새 Nest HTTP에서 달력/상세 조회 후 종료했다. 계약/migration과 승인 기준은 변경하지 않았다.

한 검토/한 작품, 수동 매핑·실행, partial coverage다. 다국가 전체 DB 장애 원자성/전수 수집/OS 격리/독립 통합 PASS는 보장하지 않는다. 질문: 같은 작품의 다른 플랫폼·국가·시즌에는 왜 별도 eventKey가 필요한가? 검토가 최신이라는 것과 출처의 최신성이 같을까?

관련 코드/정책/제공처 문서가 바뀌면 원본과 이 주장을 다시 검토한다.

고정 코드222f67f의 별도 Volta 리뷰는 추가 지적 없음을 보고했다. 임시build/39 scoped 검사를 수행했고 실제PostgreSQL은 실행하지 않았다. [범위 기록](../../../reviews/2026-11-09-reviewed-publish.md)을 참조한다.
