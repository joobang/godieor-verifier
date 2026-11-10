# INT-01A · 독립 API 관찰점 연결
- 상태: API component 검사 구현·실제실행·자기검사 완료, 독립 재검토 후 담당해제. 전체제품통합검사 아님.
- 기준: app423dd64, verifier7d84304, backendf378ac8. 요구사항 GD-005/006/007/008 및 GD-002 관찰점(승인초안).
- 범위: verifier가 작성한 가상provider 입력→실제Nest/임시PostgreSQL→날짜/정체성/필터 HTTP assertion, 개별실행 로그/receipt/v2 연결.
- 실패사례: 제목동일병합·재수집중복·정정새ID·연기취소누락·미정달력배치·UTC자정생성·KST날짜경계·DST·필터OR/AND·커서누락·검사실패누락.
- 기준 승인/ID/필수검사 변경 없음. 필터의 오래된초안과 최신정책차이는 부분검사로 분리하고 전부PASS로 위장하지 않는다.
- LEARN-ID: LEARN-0016 예정.

## 진행 기록
- verifier 원본 api-checks.cjs 및 입력/기대값 출처 fixtures/api/README.md 작성. 제품 fixture/기대값/정규화함수를 정답으로 가져오지 않음.
- 개별 Node suite의 실제 exit+마지막 JSON receipt를 바인딩. receipt누락/다른suite/0assertion/잘못된scope는 ERROR. 필터부분검사는 성공SKIPPED, 실패FAIL/timeoutERROR로 보존.
- scripts/self-test.sh 89개통과. 실제실행 첫요청은 자동승인서비스의 DNS/502 오류로 시작되지 않음. 동일요청 재시도 승인 후 실행시작, 승인검토를 우회하지 않았음.
- 독립 reviewer Fermat(01a1c2fb-2f81-7f61-9b65-abba4cee6dc5, fork_context=false) 읽기전용 코드 검토 중.


## 실제 실행/최종 결과
- 마지막 run /private/tmp/godieor-api-c24b082a. app423dd644c37f8bd2ef29e16462cd7865329a1831 / backendf378ac8(전체SHA는evidence). verifier7d84304+당시dirty/state hash. 실행기예외처리 최종1줄 수정 전의 실행이며 최신커밋실행으로 재라벨하지 않는다.
- Node24/경계probe/iOSunsigned/dependencies/generate/tsc/backend47tests/migration/3API suite/database-smoke 전부exit0. 임시DB잔존없음 docker ps 확인.
- event-identity 92 assertions, time-semantics76, api-filter-observations57. 12월동일제목의다른작품2건 및 동일externalId/다른variant 시즌3도 포함. 실제provider입력/계정데이터가 아니라 verifier synthetic이다.
- evidence에서 ios-build/event-identity/time-semantics PASS (identity/time은backend-api-synthetic scope). filter-intersection 성공은부분SKIPPED, settings-roundtrip/provider-contract/ios-user-flow/secret-check도SKIPPED로 전체ERROR. reviewPENDING, isolation_verified=false 유지. 승인초안/ID/필수검사 변경없음.
- 최종 scripts/self-test.sh 90개 통과. reviewer의receipt중첩 RecursionError 지적 수정/회귀추가. 이예외경로만 변경후 전체검사 재실행, 동일정상APIrun 반복하지 않음.
- Fermat는 정상/variant무시/제목병합 모형에서 실제CollectionService·normalize+메모리저장소/HTTP모형으로92assertion 및 변이실패를 확인. 실제PG장기run은 reviewer가 실행하지 않았다. 원본리뷰응답은 분리컨텍스트이며 구현카드/학습미열람.
- 산출물사본 work/handoff/godieor-api-c24b082a, 사용법 docs/api-checks.md, LEARN-0016. 다음: 필터최신계약/초안관찰점정리 제안 유지, iOS흐름·설정·실제출처·비밀검사 후속. 전용계정방식은 재개하지 않음.
