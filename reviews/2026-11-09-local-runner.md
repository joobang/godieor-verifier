# VFY-03/04 초기 실행기 독립 리뷰

구현 담당이 reviewer Peirce(01a1bf1e-ad14-7353-9f4c-e3dbcaa85c18, fork_context=false) 응답을 요약 전사한 기록. base ea96c2f와 dirty diff를 read-only 검토. 구현대화·작업카드·학습기록 미열람.

발견/처리: Git fsmonitor 호스트 실행(P1), replace/로컬export속성 추출변경(P1), 대소문자/Unicode 경로충돌(P2), docker run timeout 후 cleanup누락(P2), 누락object promisor remotehelper 호스트실행(P1)을 수정. reviewer가 임시repo/marker 재현과 수정 후 대조실험·62개 자기검사를 수행했다. 최종 추가 실행코드 결함 없음 보고는 아래 open finding을 해결했다는 뜻이 아니다.

OPEN P5(P2): fork+setsid 후손은 최초 processgroup cleanup으로 제거되지 않는다. reviewer가 policy=None의 가상자식으로 재현하고 별도정리했다. sandbox 적용상태에서는 독립재현하지 못했다. docs/runner.md의 초기구현/수명한계 및 isolation_verified=false 유지.

실제 canary/dependency/Prisma/backend/DB/iOS 실험은 reviewer가 재실행하지 않았다. 작성자 실제 마지막 iOS제한빌드는 실패하며 결과를통합PASS로 표현하지 않는다. 승인·verdict 생성 없음. 실제출력은 카드와 로컬 산출물참조.
