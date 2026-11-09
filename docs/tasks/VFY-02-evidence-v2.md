# VFY-01/02 · 관찰점과 evidence v2
- 상태: 관찰점 제안·v2 구현·자기검사·독립 정적 재검토 완료. 담당 해제.
- 요구사항: VFY-01/02, GD-001~010 초안. 승인 기준 원본 변경 없음.
- 기준: verifier da31fa2, app cdd8532, backend f051b95. 별도 verifier 브랜치에서 순차 작업.
- 범위: 앱/백엔드/계약/migration/기준/verifier 조합 바인딩, v1 호환·downgrade 거부, parser/회귀 검사·가상 예제·문서.
- 예상 실패: backend만 변경/계약변경/마이그레이션변경 시 이전 check/review 재사용, 부분 바인딩, schema1로 위장, 필수 검사 누락/실패/실행 오류.
- LEARN-ID: LEARN-0013 예정. runner/OS 격리/기준 승인은 후속.

## 진행 기록
- v2 subject 모듈·engine 분기·review-v2 schema·가상 예제 구현. v1 호환과 v2 downgrade 거부.
- scripts/self-test.sh: 기존33개+v2 12개=45개 통과. v2 검사에는 대상별 변경/부분 갱신/잘못된 SHA·필드·누락·실패·환경 오류·낮은 schema 위장이 포함된다.
- CLI 가상 v2: REVIEW_REQUIRED, exit2 및 work/demo-v2/report.json 생성. 기준 초안/fixture이며 제품 통과 기록 아님.
- requirements/proposals/vfy-01-observation-map.md 작성. 기준 초안과 실제 정책 차이는 제안으로 유지, acceptance 파일·승인 상태 변경 없음.
- 독립 reviewer Boyle (01a1bf16-040c-79e2-ab86-b6acb8d430ee, fork_context=false) 재검토 진행 중. OS 격리된 검토라고 주장하지 않는다.

## 독립 리뷰 후 수정
- P1: v2 전용필드를 전부 제거하면 정상v1과 식별 불가. 호출자 required_schema_version 및 CLI --require-schema-version 2로 통합 최소버전을 강제. default1은 앱전용 호환일 뿐 통합판정으로 사용 금지.
- P2: subject binding 선검사로 첫 오류가 뒤FAIL 기록을 숨김. binding을 각 check/review 평가 위치로 옮겨 검사별 오류집계를 유지.
- 추가 회귀 및 CLI 검사를 포함해 scripts/self-test.sh 최종48개 통과. 가상v2+최소schema2 CLI는 exit2 REVIEW_REQUIRED.
- acceptance SHA256 c4906283810c8b378800b67930028685a41b6a051923ea9f9415346b2d657063 유지. 승인 상태·필수 검사 변경 없음.
- LEARN-0013: docs/learning/entries/0013-evidence-subject-binding.md.

최종 코드 d15601e2911885daf09ea07672c9b9c6edbadad1. 별도 reviewer는 수정 뒤48개 검사와 API/CLI 재현, 추가 지적 없음 보고. 다음 VFY-03 snapshot/build 사본·일회용 DB 및 VFY-04 runner. 통합PASS 없음.
