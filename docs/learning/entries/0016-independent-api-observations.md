# LEARN-0016 · 독립 기대값과 API 판정 연결

작성자해설초안. 원본 docs/tasks/INT-01-api-checks.md·docs/api-checks.md, 입력/기대값 src/godieor_verifier/api-checks.cjs.

기존 smoke는 DB→Nest→API 연결만 확인했고 GD별검사를실행했다고 볼수없었다. 독립적으로 작성한synthetic provider입력과 명시적인 기대날짜/집합을 넣어 CollectionService→PostgreSQL→HTTP까지 검증한다. 불투명ID는 동일/차이 비교에만 사용하고, 구현출력·제품fixture를 정답으로복사하지 않는다.

날짜only값이 시간대에 따라 이동하지않는지, KST일/월넘김과 LondonDST에 기대문자열을 직접 썼다. 재수집ID보존·같은제목다른작품·시장/시즌variant보존·정정/연기/취소 및 수집실패데이터보존은 정상응답몇건만보는것보다구체적인관찰점이다. 그결과가 실제제공처데이터나 iOS화면의 정답까지증명하지는않는다.

각suite는 분리된명령으로실행하고 실패를보존하며 다른suite를계속한다. exit0만으로 PASS를만들지않고 suite/scope/assertions receipt까지검사한다. receipt자체도 서명/실행격리의증명은아니므로 검토한고정코드·실행로그·v2조합binding과 함께사용한다.

필터의최신계약(서비스/기기는해당분야내적용)과 예전초안의전역AND문구가 달랐다. 기준을몰래바꾸거나 일부예제성공을 전체PASS로올리지않고 별도관찰단계로남겼다. 추가관찰점제안·승인기준·실제실행을 구분한다. 정밀도/필터정책/API계약이변경되면 관련기대값과해설을재검토한다. 성능향상·전수coverage·사용자학습완료는측정하지않았다.
