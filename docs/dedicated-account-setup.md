# 전용 macOS 검증 계정 준비

2026-11-10 사용자 선택: 이 Mac의 별도 표준 사용자로 iOS 자동 검증 빌드를 실행한다.
계정명 제안은 `godieorbuild`, HOME 제안은 `/Users/godieorbuild`다. 아직 계정은 없다.

## 개인 iPhone 설치와의 관계

기존 `dojoohwan` 계정의 Xcode에서 Apple ID/Personal Team을 선택하고 iPhone을 연결해
설치·디버깅한다. 인증서·개인 키체인·기기 신뢰 설정을 검증 계정으로 복사하지 않는다.
자동 검증 계정에서는 서명하지 않는 generic Simulator 빌드를 먼저 검사한다.
현재 `app/scripts/build-ios.sh`도 `CODE_SIGNING_ALLOWED=NO`와 Simulator를 사용한다.
따라서 전용 계정을 만든다는 이유로 iPhone 설치용 Apple ID를 새로 만들 필요는 없다.
실제 iPhone 설치/서명은 별도 확인이며 이 문서가 성공을 보장하지 않는다.
실기기의 API 주소는 Mac의 localhost가 아니라 휴대폰에서 접근 가능한 주소/HTTPS여야 한다.

## 계정 생성

관리자 인증이 필요하므로 macOS 시스템 설정의 **사용자 및 그룹 → 사용자 추가**에서
새 사용자를 **표준**으로 생성한다. 계정 이름과 HOME을 확인하고 비밀번호는 macOS 입력란에서만
설정한다. 관리자 권한·Apple ID/iCloud·자동 로그인·개발자 인증서·개인 비밀을 추가하지 않는다.
현재 세션을 로그아웃할 필요 없이 생성할 수 있지만, 전용 사용자 환경 검사는 해당 계정에서
로그인한 뒤 수행한다. 새 UID는 실제 생성 결과를 사용하며 502 등으로 가정하지 않는다.

아직 계정 생성 UI 조작이나 관리자 인증을 요청하지 않았다. 이 절차는 준비 문서다.

## 생성 후 실행 순서

1. 실행자 UID/HOME과 Darwin T 물리 경로를 전용 사용자 세션에서 확인한다.
2. 검증기와 고정 앱 snapshot/build 사본만 전용 staging으로 전달한다.
   개인 HOME 전체 권한을 열거나 원본 저장소를 공유해서 접근 오류를 해결하지 않는다.
   staging 전달 자동화와 단일 run 잠금은 아직 미구현이다.
3. 전달된 검증기에서 `scripts/check-isolated-ios-host --caller-uid 501 --caller-home /Users/dojoohwan`.
   성공해도 사전 조건만 확인한 것이며 접근 차단/빌드/수명 검증 성공은 아니다.
4. 일반 및 `--sandbox` Foundation probe 비교 후 전용 사용자의 Darwin T에 한정한
   권한 검토를 진행한다. 현재 runner 프로필에는 전용 Darwin T 허용이 구현돼 있지 않다.
5. 제한 Xcode 빌드, 원본/비밀 canary 차단, 네트워크/Docker socket 차단 및 후손 수명 게이트를 검사한다.
   UID 분리만으로 setsid 자식 정리가 해결되지는 않는다.

계정 생성 뒤에도 실제 게이트가 모두 검증되기 전까지 isolation_verified=false,
P5 open, 통합 PASS 없음으로 유지한다.
