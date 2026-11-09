# 로컬 파이프라인 독립 검토·검사 제안

미승인 초안. acceptance.yaml과 verifier 엔진은 변경하지 않는다.
입력은 고정 backend SHA, 계약·migration·Prisma schema digest, 가상 데이터 표시와 제품 정책이다.
작성자 실행 기록을 정답 fixture/독립 검증으로 재사용하지 않는다.

확인할 반례: scope fetch/정규화/DB publish 실패 후 이전 성공 데이터 보존, 중복 외부 키·다른 provider의 이름 같은 팀,
같은 자료 재수집 시 Event ID/변경 이력 유지, 같은 provider 중복 실행, DB CHECK/FK 우회,
날짜만 값과 KST/DST 변환, 페이지 중 revision 변경/커서 위조·만료, 개인 경계의 인증 우회 차단.
최소 service/device 검사·source origin/범위·회차 유입을 포함한다. 실제 source가 연결되지 않은 상태를 실데이터 PASS로 표시하지 않는다.
현재는 작성자의 local 실행뿐이다. 실행 경계/일회용 검사 DB/실제 runner·evidence v2/독립 review가 후속 작업이다.
제품 테스트는 이번 요청에서 추가/실행하지 않았다.
