# 초기 구성 확인 · 2026-11-06 KST

| 확인 | 실제 결과 | 범위/한계 |
|---|---|---|
| iOS 시작 프로젝트 | `scripts/build-ios.sh` exit 0, BUILD SUCCEEDED | 서명 없는 Simulator SDK 대상 빌드. Simulator 실행·사용자 흐름 검사는 아님 |
| Xcode 프로젝트 파일 | `plutil -lint ios/GODIEOR.xcodeproj/project.pbxproj` exit 0 | 파일 형식 검사 |
| 판정 엔진 | `scripts/self-test.sh` exit 0, 33 tests OK | 합성 evidence를 사용하는 엔진 자체 검사 |
| 예제 CLI | exit 2, REVIEW_REQUIRED, JSON/Markdown report | draft 기준 + fixture + 미검증 격리. 제품 실행 결과 아님 |
| 독립 bootstrap 리뷰 | 4건 발견 → 수정 → 원래 재현으로 독립 재확인 | [리뷰 기록](../reviews/bootstrap-2026-11-06.md) |
| 문서 내부 링크 | 존재하지 않는 상대 경로 0건 | 초기 Markdown 파일 대상 |

개발 환경: Xcode 26.6 (17F113), Swift 6.3.3, Python 3.9.6.
첫 Simulator 장치 조회는 현재 sandbox에서 CoreSimulator 접근 오류가 났다.
일반 Simulator SDK 대상 컴파일은 성공했지만 실제 Simulator 실행을 확인했다고 표현하지 않는다.

초기 검사 당시 두 저장소 모두 미커밋이었다. 실행 시작·종료 시각을 완전하게 수집하는
runner도 아직 없다. 이 문서는 정식 제품 verification run이 아닌 초기 설정 확인 기록이다.
관련 코드의 digest는 [파일 manifest](../reviews/bootstrap-source-manifest.json)에 있다.

원시 로그/데모 report는 각 저장소 `work/bootstrap/`에 있으며 Git에서 제외된다.
자동 snapshot·runner·AI 어댑터·검증된 실행 권한 경계와 승인 기준을 연결하기 전에는 제품 PASS를 주지 않는다.
