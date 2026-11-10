# INT-01A · 독립 API 검사

verifier src/godieor_verifier/api-checks.cjs가 자체 작성한 가상 제공처 입력을 실제 CollectionService/Repository에 주입한다. 실제 제공처 연결 검사가 아니다. 기대값은 제품 출력·제품 fixture에서 복사하지 않고 계약과 날짜 규칙에서 작성했다. 런타임 opaque ID는 동일성/차이 비교에만 사용한다.

## 검사 범위

- event-identity: 다른 시장·같은 작품의 다른 날짜·시즌/서비스·기기별 이벤트 구분, 복수 서비스 단일 이벤트, 재수집 ID·페이지 안정성, 정정 후 같은 ID와 이전 날짜, 연기/취소, revision 충돌409, 수집실패 시 마지막 성공시각·기존데이터 보존.
- time-semantics: 명시적 KST 날짜넘김/05:00, date_only가 UTC/Seoul/Los_Angeles에서 동일하고 instant필드를 만들지 않음, 미래분기/연도미정은 undated에만,2025범위제외, London DST spring gap/fall fold, 월경계·반개구간.
- api-filter-observations: 차원 내부 OR, 카테고리 선택 및 OTT/기기별 포함·제외, 국가·EPL 전세계표시, 부적합값400. 최신계약의 분야내 필터 적용과 예전acceptance의 전역AND 문구가 달라 이 단계 성공은 filter-intersection 전체PASS가 아니라 SKIPPED+coverage로 남긴다. 실제실패/timeout/receipt오류는 FAIL/ERROR로 보존한다.

각 suite는 독립 Node 프로세스이며 새 앱 context를 열고 같은일회용DB에 자기입력을 다시 publish한다. Docker/migration은 verifier가 관리한다. suite 실패가 다음 suite 실행을 숨기지 않도록 개별 결과를 수집한다. 이후 기존 기본smoke도 별도로 실행한다.

## 판정 연결

event-identity/time-semantics는 API component 검사 결과로 연결한다. UI 표시는 별도 ios-user-flow가 여전히 필요하다. 로그의 마지막 JSON receipt에 schema/suite/status/scope/assertions가 정확히 있고 exit0이며 timeout이 없어야 PASS. 잘못된/없는receipt는 ERROR, nonzero는FAIL, timeout은ERROR. 모든 check는 run·app·backend·계약·migration·기준·verifier subject에 묶인다.

현재 기준은 draft이며 iOS흐름·설정서버왕복·실제제공처·전체비밀검사는 이 suite가 대신하지 않는다. 성공한 backend검사를 앱·제공처·제품통합PASS로 확대하지 않는다. 로컬실행은 docs/local-verification.md를 따른다.
