# LEARN-0017 · 비밀 검사 정책과 UI 관찰 범위

작성자기술해설초안. 원본 docs/tasks/INT-01-secret-check.md·docs/secret-check.md. 실제결과는 고정run의logs/evidence가소유한다.

비밀검사는 하나의정규식으로 “아무비밀도없음”을증명하는것이아니다. literalcredential과라벨PII를정의하고 input/source/fixture/log/bundle 범위를명시한다. 파일누락·읽기오류·symlink는성공으로추정하지않는다. 좁은negativefixture예외는 파일hash/root/경로/exactmatch로고정한다.

독립review에서 rglob가권한오류를숨기는것, binary/XMLplist를문자열로만펼치면 key/value라벨관계가소실되는것, 값이파일명에들어있으면finding경로로노출되는것, root조상link우회, Python bool/int동등비교로잘못된receipt를받는것을재현했다. 각각 os.walk onerror·구조JSON보존·path_id만기록·조상검사·정확int검사로수정하고회귀를추가했다. 내용뿐아니라경로도literal검사한다.

최종107자체검사와실제run의182inventory항목검사를확인했다. 파일명이원문으로노출되지않지만 위치는pathhash와line/rule로복원할수있다. 이결과는 암호화·압축·분할비밀이나 불특정개인정보전수추론의증명이아니다.

별도CUA에서 가상계약응답→달력날짜→목록→상세, 국가/시간대/OTT변경후프로세스재실행복원을확인했다. 이것은 AppStorage/화면component관찰이며 Google계정서버설정동기화의검사가아니다. 따라서 설정서버왕복·전체UI기준을PASS로승격하지않았다. 자동판정된scanner와작성자UI관찰을구분한다. 향후scan정책/fixture예외/UI·서버설정계약이바뀌면본문주장을재검토한다.
