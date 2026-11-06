# Bootstrap 독립 리뷰 기록

- 범위: 판정 엔진·입력 계약·자기 검사. 제품 기능 검증/acceptance 승인 아님.
- 대상 상태: 최초 commit 이전의 로컬 파일. 고정 commit SHA 검증을 수행한 것은 아님.
- 컨텍스트: 구현 대화를 넘기지 않은 별도 에이전트. `fork_context=false`.
- 모델: 도구의 상속 설정 사용. 도구 결과에 정확한 모델 식별자가 노출되지 않아 임의로 기록하지 않음.
- 격리: 별도 AI 컨텍스트이며 별도 OS 사용자/권한 격리는 아님.
- 원본 코드 식별: `bootstrap-source-manifest.json`의 파일 digest 참조.

## 최초 검토: 자체 검사 24개 이후 발견

| ID | 심각도 | 확인한 문제 | 최소 재현 | 수정 확인 |
|---|---|---|---|---|
| BOOT-001 | high | 개별 검사에 SHA·기준 binding 없음 | app/review head만 변경하고 이전 checks 유지 | run ID·head SHA·기준 digest binding 추가, 불일치 ERROR |
| BOOT-002 | medium | 리뷰 스키마와 엔진 형식 검사 불일치 | settings 배열/추가 필드/PENDING 필수값 삭제 | 필드·타입 검사 추가, 모두 ERROR |
| BOOT-003 | medium | 중첩 JSON·잘못된 Unicode로 CLI 크래시 | 1100단 중첩, 고립 surrogate | ERROR(3), JSON/Markdown report, atomic write |
| BOOT-004 | medium | 앞 검사 형식 오류가 뒤 FAIL을 숨김 | 첫 command 삭제, 다음 FAIL | 검사별 오류 수집, 순서 양쪽에서 failures 보존 |

합성 PASS 분기의 재현은 테스트에서 메모리로 만든 가상 승인/실행 데이터만 사용했다.
실제 `acceptance.yaml`은 계속 draft이며 승인자를 작성하지 않았다.

## 독립 재검토

기존 재현을 먼저 재실행한 뒤 33개 자기 검사를 수행했다. 모두 통과했고,
위 4건은 원래 재현 절차에서 해결됐음을 독립 reviewer가 확인했다.
추가 객체/null settings, 잘못된 findings 타입, 추가 finding 필드,
중복 JSON 키와 비정상 숫자는 ERROR로 확인됐다. 이 범위의 추가 잘못된 PASS/크래시는 보고되지 않았다.

이는 해당 사례의 수정 확인이다. 임의 evidence의 진위나 OS 격리를 입증하지 않으며
제품 PASS 또는 검증 시스템 V1 전체 완성의 근거가 아니다.

## 실행 근거

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B \
  -m unittest discover -s tests -v
```

reviewer는 최소 재현을 메모리와 임시 디렉터리에서 실행했고 저장소 파일을 수정하지 않았다.
현재 재현을 보존하는 자동 검사는 `tests/test_engine.py`에 있다.
로컬 자체 검사 로그: `work/bootstrap/self-test.log`. 로그는 Git에서 제외하고 코드와 명령으로 재현한다.
