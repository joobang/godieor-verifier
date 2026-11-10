# 로컬 snapshot·검사 실행기

현재 실행정책은 [기존 계정 검증](local-verification.md)이 원본이다. 2026-11-10 사용자 지시로 전용계정/계정전환 방식은 폐기했다. 기존계정에서 서명없는 iOS 고정빌드와 backend·임시DB 검사를 진행한다.

- scripts/runner: 고정 SHA snapshot/build 분리, 계약·migration·v2 binding, 명령·exit·timeout·로그hash.
- source는 rawGit tree/blob 추출. hooks/fsmonitor/replace/lazyfetch/transport 차단, symlink/submodule/LFS/Unicode·대소문자충돌 거부.
- backend는 최소환경 sandbox. iOS는 기존계정 local-reviewed 모드로 고정 xcodebuild 명령 실행, isolation_verified=false 유지.
- 일회용DB는 고유컨테이너·tmpfs·동적loopback포트이며 생성시도부터 finally cleanup. 기존 제품DB/볼륨을 사용하지 않는다.
- 실제 ios-build 결과는 PASS/FAIL/ERROR, 미실행필수검사는 SKIPPED. 전체검증·기준승인·리뷰까지 충족했다고 오해하지 않는다.

과거 Foundation atomic쓰기/전용UID/후손수명 진단은 역사적기록이다. 해당인증경로 복구나 계정추가를 다음필수작업으로 제안하지 않는다. source분리/chmod/최소HOME가 OS격리를 보장하지 않는다는 경계는 유지한다. 사용법·현재제약은 위 원본문서를 읽는다.
