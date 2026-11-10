# LEARN-0018 · 공개/계정 API의 주소 설정 일치

작성자해설초안. 원본 app/docs/ai/tasks/APP-AUTH-10.md 및 ios/GODIEOR/PublicAPI.swift·Account.swift. 실제iPhone장애재현은아니며 정적설정불일치를발견한수정이다.

계정클라이언트는 env와Info.plist를읽었으나 공개클라이언트는env만읽었다. 빌드설정HTTPS주소가계정요청에는적용돼도 달력요청은기기의localhost로향할수있었다. 공유resolver로 env→bundle우선순위를통일하고 기기에서는localhostfallback을제거했다. Simulator공개조회만개발loopback을허용하고 계정토큰요청은HTTPS를유지한다. 잘못된명시override를숨겨다른주소로fallback하지않는다.

독립리뷰에서유효한대문자scheme·LOCALHOST가거부되는회귀를찾아비교정규화와회귀입력을추가했다. 순수Swift검사·unsigned iOS전체빌드와 reserved테스트주소의실제Info.plist주입검사를작성자가수행했다. reviewer는Swift/diff검사를별도로수행했으며 실기기Google로그인이나전체통합PASS를판정하지않았다.

앱아이콘실행에는Xcode Run환경변수가유지되지않으므로 빌드의Info.plist주입경로도검사해야한다. 실제HTTPS주소/개발CA신뢰/Google자격증명은 별도실환경조건이다. 주소해석·Info키·프로토콜정책변경시이기대값을재검토한다. 성능개선이나실기기OAuth성공은측정하지않았다.
