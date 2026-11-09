# LEARN-0014 · 고정 소스와 실제 실행의 경계

작성자 기술 해설 초안. 원본 docs/tasks/VFY-03-04-runner.md, 사용법 docs/runner.md. 통합PASS/학습 성과/성능 개선을 주장하지 않는다.

SHA 문자열만 지정해도 Git replace ref나 로컬 export속성이 추출 결과를 바꿀 수 있었다. 독립 리뷰에서 가상marker/임시repo로 재현했다. raw tree/blob 읽기, replace금지로 바꾸고 로컬속성을 적용하지 않는다. fsmonitor가 status 단계에 호스트 프로그램을 실행하거나, promisor의 missingobject 조회가 remote helper를 실행하는 문제도 재현돼 Git 환경·설정·모든transport를 차단했다. 경로는 Unicode와 대소문자충돌을 선제거부한다.

읽기 전용snapshot은 빌드사본과 분리한다. chmod는 동일사용자 OS격리가 아니다. 최소HOME·제한sandbox에서 가상canary/원본 접근·snapshot읽기/쓰기·build쓰기를 실험했고 제한된허용/거부만 확인했다. 이결과를 isolation_verified=true로 확장하지 않는다. setsid후손은 최초processgroup을 벗어나므로 전체수명정리는 여전히 미해결이다.

실행기는 digest고정PostgreSQL 이미지를 기존DB와 다른 tmpfs/동적loopback포트로 실행하고 고유컨테이너명으로 정리한다. run응답timeout도 생성시도부터 cleanup을 시도하도록 수정했다. 이timeout경로는 mock회귀검사이며 실제Docker 장애주입은 아니다.

실제 제한실행에서 backend47개검사와 새DBmigration/반복수집ID/달력·상세smoke를 수행했다. iOS 제한빌드는 임시쓰기 경계문제를 드러냈고 당시실행을 실패로 기록했다. 원본환경에서 과거빌드가 성공했다는 사실로 이실행의 실패를 덮어쓰지 않는다. 실행한단계와 전체GD승인검사는 별개이므로 부족한필수검사는 SKIPPED→ERROR로 남긴다. 관련Git·실행정책·런타임이 바뀌면 이주장을 재검토한다.
