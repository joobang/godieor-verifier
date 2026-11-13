# LEARN-0011 · 공식 공지 근거와 제품 이벤트 식별자를 분리하기

2026-11-09, 실제 개발 선택과 예방 설계·작성자 실행 기록. 운영 장애/성과 수치·사용자 이해도는 기록하지 않는다.

공지URL은 출처 근거이고 작품/공개 사건 식별자가 아니다. 제목·날짜·시즌에서 키를 만들면 날짜 정정 때 새 이벤트가 생기거나 같은 제목이 섞일 수 있다. 이를 예방하기 위해 수동 고정 contentKey/eventKey와 현재 검토 revision을 별도로 입력한다. backend ADR-013 / DATA-02B / docs/reviewed-publish.md가 원본이다.

기존 CollectionService/Repository의 provider key 매핑·scope 트랜잭션을 재사용했다. 후보 writer lock은 검토 파일 변경을 막고 provider advisory lock 안의 Client identity 비교는 기존 국가/플랫폼/작품/알려진 시즌 덮어쓰기를 거부한다. 미정 시즌에 번호를 보완할 수 있지만 다음 시즌은 새 eventKey가 필요하다. 시간대가 없으면 날짜만 보존하며 게시일을 sourceUpdatedAt으로 만들지 않는다.

작성자 실행: 전체47개 자체 검사, 일회용 PostgreSQL에서 반복 ID·날짜 정정·미정→확정 시즌·변경 거부·stale/불완전 입력 보존 확인. 공식 공지4건을 로컬DB로 수동 반영하고 재실행 후4건/최초변경이력4 유지, 기존 fixture7건 보존. 새 Nest HTTP에서 달력/상세 조회 후 종료했다. 계약/migration과 승인 기준은 변경하지 않았다.

한 검토/한 작품, 수동 매핑·실행, partial coverage다. 다국가 전체 DB 장애 원자성/전수 수집/OS 격리/독립 통합 PASS는 보장하지 않는다. 질문: 같은 작품의 다른 플랫폼·국가·시즌에는 왜 별도 eventKey가 필요한가? 검토가 최신이라는 것과 출처의 최신성이 같을까?

관련 코드/정책/제공처 문서가 바뀌면 원본과 이 주장을 다시 검토한다.

고정 코드222f67f의 별도 Volta 리뷰는 추가 지적 없음을 보고했다. 임시build/39 scoped 검사를 수행했고 실제PostgreSQL은 실행하지 않았다. [범위 기록](../../../reviews/2026-11-09-reviewed-publish.md)을 참조한다.


## DATA-47 후속 관측 · 2026-11-13 (구현 담당 기록)

실제 로컬 검토에서 후보와 게시 경로의 분류 범위 차이가 드러났다. lineup 후보는 documentary를 보존하지만 reviewSchema와 Canonical/API 게시 분류에는 documentary가 없었다. 공식 다큐 시리즈를 포함한6건은 저장 전 검증에서 거부됐고, 구현 담당은 후보state가 백업과 바이트 단위 동일하며 매핑57개도 그대로임을 확인했다. 실패 배치의 DB publish는 실행하지 않았다.

현재 지원되는5건만 별도 검토·게시해 같은11~12월KR 범위55→60건을 확인했다. 유형 지원이 없는1건은 보류했다. 공식 근거의 충분성, 입력 스키마 지원, 제품/API 표현 가능성은 각각 확인해야 한다. 한 enum만 늘리거나 실제 다큐를 다른 종류로 바꿔 통과시키는 것으로 해결하지 않는다.

이 기록은 작성자 실행 사실이며 독립 검증·승인·운영 장애·성과 측정이 아니다. 원본은 backend [DATA-47](../../../../godieor-backend/docs/tasks/DATA-47-netflix-official-recovery.md)와 [게시 절차](../../../../godieor-backend/docs/reviewed-publish.md)다. 유형 지원 코드/계약이 바뀌면 이 경계를 재검토한다.

## DATA-49 후속 관측 · 2026-11-13 (구현 담당)

유형지원코드를추가한DATA-48과실제DB반영은별개였다. DATA-49는로컬주소/기존62행/적용migration을확인하고새migration적용후현재revision의다큐시리즈형태를명시검토해1건게시했다. KR11/12저장관측과오늘공식Tudum·title형식/시즌근거를구분했으며해외일자를KR근거로대체하지않았다. 전후SQL로기존62event전체row를비교하고재게시이벤트63/신규변경1유지를확인했다. 기간61건은특정로컬범위의관측이며전수수집률/독립PASS/실폰확인을뜻하지않는다. 원본 backend DATA-49/evidence/data49, ADR013/017. 기존secret검사finding과독립승인은미해결이다.
