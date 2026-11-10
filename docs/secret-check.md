# Literal 비밀 검사 · INT-01B

GD-010의 scanner component다. **명시한 literal 패턴과 라벨된 개인정보 검사이며 임의 개인정보·암호화/분할/인코딩된 모든 비밀 부재의 증명은 아니다.** 기준초안이나 필수검사 목록을 변경하지 않는다.

## 입력과 판정

실행기의 고정 app source/backend source/backend data fixtures/완료된 단계 logs/빌드 GODIEOR.app 번들을 검사한다. 원본 개인HOME·.env·키체인은 수집하지 않는다. 원문매치·원래파일명은 출력하지 않는다. 결과는 root label, 상대경로 SHA256(path_id), rule, 위치, 파일digest·크기만 보존한다. 파일명에 credential이 있을수있어 경로도해시화하고 경로literal검사도한다. 로컬에서문제파일을찾을때는 상대경로hash와 inventory를대조한다.

주요 규칙은 private-key PEM, AWS/GitHub/OpenAI/Google/Stripe 식별prefix, JWT, 명시 credential 할당, password포함URL, 한국주민번호형식후보, email/phone라벨이다. 정상적인 public client ID·임의엔트로피문자열은 전체가 비밀이라고 단정하지 않는다. raw binary ASCII, UTF16 BOM, XML/binary plist를 검사하며 plist는 key/value라벨을보존한다. zip/compressed resource 해독이나 일반명사로 저장된 민감정보 전수추론은 범위밖이다.

root누락·빈root·읽기불가 디렉터리/파일·64MiB초과·비정상plist·사용자symlink 및 조상symlink는 ERROR다. /tmp,/var,/etc의 macOS정규시스템별칭만허용한다. os.walk onerror로 권한오류를 조용히건너뛰지않는다. 파일시스템격리/악성동시교체방지의 보안증명은 아니다.

파일/오류없음은PASS, 탐지는FAIL, 입력/읽기오류는ERROR. 마지막receipt는정확한field/type/policy/scope/count를검사하고 실패·timeout·누락·과도중첩JSON을성공으로추정하지않는다. 결과 secret-findings.json, 로그 secret-check.log(스캔입력logs와분리), v2 subject binding으로저장한다.

## 좁은 예외

- `.env.example`의 정확한두문자열 replace-with-local-random-value / replace-with-at-least-32-random-bytes와 `${identifier}` 전체템플릿은 literal비밀이아니다. 임의 starts-with 예외는없다.
- backend tests/reviewed-publish.test.cjs의 `https://user:password@...`는제공처URL거부를확인하는합성negative입력이다. 파일전체SHA256·root·경로·exactmatch를모두고정한예외만허용하고 inventory에적용을명시한다. 같은값이다른파일/변경된파일에있으면탐지한다.
- example.com/org/net 및 .test/.invalid 라벨email은예약된예제다. 일반개인도메인은예외가아니다.

예외가있는파일이바뀌면일단탐지되며 실제이유를검토해야한다. 결과를통과시키기위해 파일전체·폴더전체를무조건제외하지않는다.

## UI/설정 확인과 구분

scripts/ui-contract-stub.py는수동Simulator검사용가상계약응답이다. 실제 backend나제공처연동을검사하지않는다. 국가/시간대/OTT로컬설정의재실행복원은 AppStorage component관찰이며 Google계정서버 roundtrip이나 전체 ios-user-flow PASS가아니다. 이번관찰은 작업카드에따로기록하고 필수settings-roundtrip/ios-user-flow는미완료로유지한다.
