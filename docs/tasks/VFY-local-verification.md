# VFY-LOCAL · 전용 계정 폐기와 기존 계정 검증
- 상태: 전용계정 방식 폐기·로컬 실행 수정 및 실제 실행 확인 완료. 담당 해제.
- 사용자 확정(2026-11-10): 전용계정 검증방식 폐기, 검증로직 재검토·수정 후 다음작업 진행.
- 기준: app4630795, verifier82cfdb7. 요구사항 GD-010/VFY-03/04 초안.
- 범위: 계정전환 도구 종료, 기존계정의 검토한 고정소스/서명없는 iOS 빌드·임시DB·v2 evidence 실제실행. OS계정/ACL 자체삭제는 하지 않는다.
- 실패사례: 과거 계정 로그인 안내 재등장, sandbox 성공/일반빌드 성공 혼동, 실제실패 누락, 미실행검사 PASS 위장.
- LEARN-ID: LEARN-0015 예정. 계정격리/P5를 제품개발 필수선행으로 삼지 않되 isolation_verified=false와 기준초안/미실행 표기는 보존.


## 실제 결과 (2026-11-10 KST)
- scripts/self-test.sh 최종84개 통과. 기존계정 iOS 고정unsigned recipe, 폐기CLI, iOS실패 후backend계속/Docker실패 후iOS결과보존 회귀 포함.
- 별도 reviewer Meitner(01a1c2e7-5bae-79c2-a8b9-3f0fe7de628c, fork_context=false): 84개검사 및 모의7조합 실행, 추가결함없음 보고. 구현대화/카드/학습미열람. 실제Xcode/Docker실행은 작성자만 수행했다.
- 첫run9f37327a backend47검사 성공이나 Docker서비스꺼짐. Docker Desktop 기존설치를 시작했다. ca21c835 iOS빌드 성공 후 npm ECONNRESET. 설치성공cache재사용+prefer-offline로 재실행.
- 최종 /private/tmp/godieor-local-ad8f1b57: Node24/경계probe/iOS빌드/dependencies/generate/tsc/backend47tests/migration/database-smoke 모두 exit0. 일회용 godieor-vfy-* 컨테이너 잔존없음 확인.
- 고정입력 app4630795a7fd31b568497481d43cb3ef619f6c89f, backendbcf1f463498ae99d2e747aba97facf5e66977103. verifier82cfdb7 + 당시dirty/state hash. 최신커밋실행으로 재라벨하지 않는다. API/초기migration/acceptance 승인상태 변경없음.
- report는 ERROR: event-identity/time-semantics/filter-intersection/settings-roundtrip/provider-contract/ios-user-flow/secret-check 7개가 아직미실행·미연결. ios-build만 실제PASS. reviewPENDING, isolation_verified=false. 이결과를 전체제품PASS로 표현하지 않는다.
- 산출물사본 verifier/work/handoff/godieor-local-ad8f1b57 (Git제외). LEARN-0015.
- 다음작업: 계정격리진단이 아니라 verifier INT-01의 독립API/날짜·필터검사연결과 앱제품기능/데이터출처확장. Google실제인증/찜·계정설정 및 극장영화실데이터는 아직별도. 전용계정로그인/암호/ACL복구를 요구하지 않는다.
