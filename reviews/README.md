# 리뷰 지적 이력

현재는 수동 JSON 기록이며 engine에 자동 연결되지 않는다. 빈 ledger는 리뷰 통과 증거가 아니다.
새 리뷰마다 기존 finding을 복사해 없애지 않고 ID를 유지한다.

한 지적의 필드:

```json
{
  "id": "F-0001",
  "requirement_id": "GD-007",
  "status": "open",
  "severity": "high",
  "first_run_id": "실제 run ID",
  "app_head_sha": "실제 대상 SHA",
  "acceptance_sha256": "실제 기준 digest",
  "evidence": "실제 코드/로그 위치",
  "reproduction": "재현 절차",
  "history": []
}
```

허용 상태는 open / resolved / disputed / deferred다. resolved는 독립 재검사 근거와
대상 SHA/run ID를 history에 추가한 뒤 기록한다. 작성자의 ‘수정했다’는 답글만으로 닫지 않는다.
재검토자는 코드를 먼저 확인한 뒤 작성자 설명을 본다. 기존 지적과 같은 문제는 새 ID로 중복 등록하지 않는다.
미해결 차단 지적은 다음 review findings에도 남긴다. engine은 현재 ledger를 직접 읽지 않으므로
독립 reviewer/운영자가 누락되지 않도록 연결해야 한다.
