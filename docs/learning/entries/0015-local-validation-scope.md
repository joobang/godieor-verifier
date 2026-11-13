# LEARN-0015 · 제품 검증과 실행 환경의 범위

원본: docs/tasks/VFY-local-verification.md 및 docs/local-verification.md. 작성자 기술해설 초안.

전용UID/Darwin임시경로/P5수명격리는 무인·비신뢰코드 실행환경의 보안 과제였다. 제품의 기존Mac 빌드·서명·출시 필수조건으로 삼을 이유는 없었다. 2026-11-10 사용자가 전용계정방식을 폐기해, 검토한 고정소스에서 기존계정의 unsigned iOS 빌드를 실행하는 방향으로 바꿨다. OS계정·개인HOME ACL은 이 변경에서 삭제/수정하지 않았다.

고정snapshot·별도build사본·계약/migration/기준hash·임시DB·실행로그·독립리뷰는 유지한다. backend제한실행과 iOS local-reviewed 실행을 각단계에 기록하고 isolation_verified=false를 유지한다. 기존계정빌드성공은 OS격리검증이 아니며, 필수검사·기준승인·실제Google연동이 자동충족되는 것도 아니다.

iOS빌드를 DB/Docker 뒤에두면 Docker부재가 iOS미검사로 이어졌다. iOS를 먼저독립실행하고 그실패도 보존한채 backend검사를 이어가게 바꿨다. Docker미실행과 npm연결끊김은 실제작성자실행에서 관측했다. 실패/timeout조합은 모의회귀로 검사했다. 전용계정인증복구는 후속필수과제에서 제거했다.

향후 외부PR 무인실행을 도입할 때에는 별도환경정책이 필요하다. 그전까지 동계정검사를 권한격리나 제품통합PASS로 재명명하지 않는다. 관련실행정책·검사연결·플랫폼이 바뀌면 본주장을 재검토한다.

## DATA-48 실제 관측 · 2026-11-13

작성자 관측: Node22 working-tree 자체통과와 정식 runner 준비성공은 달랐다. 기존 계약hash drift가 고정snapshot을 막았고, 실행기의 CJS만 수집하는 glob은 ESM을 누락했다. manifest와참조를연결하고 ESM실패/빈목록/링크회귀를추가했다. 실제실행에서 가상수집비활성 때문에 smoke가빈결과로실패했고 해당단계만명시활성후통과했다. Node24 최종고정HEAD154개와과거dirty포함154개의구성은다르다. 다큐확정후새migration/API/unsigned빌드성공도secret룰FAIL·미실행필수검사·독립승인을대체하지않는다. backend DATA-48 카드·ADR016/017 및 evidence/data48이 원본. 판정규칙과승인상태는바꾸지않았다.
