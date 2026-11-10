# 독립 가상 API 입력/기대값

입력은 provider-record 계약과 제품·날짜 규칙에서 verifier가 작성했다. backend fixture 출력이나 API 응답을 복사하지 않았다. 모든URL은 example.invalid이며 origin은fixture다. 서버ID는 동일/차이 비교에만 관찰하고, 기대날짜·집합·개수는 api-checks.cjs에서 직접 지정한다.

KST날짜넘김, London spring/fall DST, UTC월말→KST다음달, date_only 불변, 미래분기미정목록, 동일제목다른작품/동일출처ID다른variant를 포함한다. 입력생성 helper와기대값은 verifier/src/godieor_verifier/api-checks.cjs에 있으며 실제제공처수집이나 전수coverage의 증거가 아니다.
