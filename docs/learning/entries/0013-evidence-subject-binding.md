# LEARN-0013 · 증거의 대상 조합 묶기

검증기 개발자 해설 초안. 원본 docs/tasks/VFY-02-evidence-v2.md 및 docs/evidence-v2.md.

앱 SHA만 고정하면 backend/계약/migration이 바뀐 뒤에도 이전 검사를 같은 결과로 오인할 수 있다. 전체 대상 선언과 기준·검증기 상태를 canonical JSON으로 묶어 subject digest를 만든다. 모든 검사와 리뷰에 같은 digest를 요구해 일부 결과만 새 대상으로 교체하는 입력을 거부한다.

입력 바인딩은 실행 증명이 아니다. 다른 사람이 선언과 hash를 모두 재작성할 수 있으므로 자동 snapshot·runner가 실제 파일/명령·로그·격리 경계를 확인해야 한다. 가상 evidence에서 합성 승인으로 PASS 분기를 검사한 것은 사용자 승인이나 제품 PASS가 아니다.

현재 48개 자기 검사 및 가상 CLI의 REVIEW_REQUIRED를 작성자가 확인했다. 실제 앱/backend 통합 실행은 이 변경 범위에 없다. source hashing 또는 runner 계약 변경 시 본 문서의 선언/진위 경계 주장을 재검토한다.

독립 리뷰에서 v2 전용필드를 전부 제거하면 정상 v1과 구별할 수 없음을 재현했다. 호출자가 최소 schema2를 강제하는 정책을 추가했다. 검사별 binding 오류를 루프 안에서 집계하여 뒤의 별도 실패가 누락되지 않도록 했다.
