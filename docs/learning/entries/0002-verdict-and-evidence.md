---
id: LEARN-0002
title: AI의 통과 선언과 실행 증거를 분리하기
kind: technique
status: draft
tags: [AI, verification, evidence, testing]
created: 2026-11-06
updated: 2026-11-06
requirements: [GD-010]
user_explanation: not-recorded
publication: private-draft
---

# AI가 ‘됐다’고 말해도 무엇을 확인해야 하나

GODIEOR 검증기 bootstrap의 구현 사례다. 운영 중 장애나 정식 제품 PASS 사례는 아니다.
AI의 리뷰는 오류를 찾는 데 쓰고, 실행 여부와 결과 집계는 프로그램으로 확인하는 구성을 만들었다.

## 풀려는 문제

AI가 ‘모든 테스트 통과’라고 쓰더라도 검사 누락, 실행 환경 오류, 이전 코드의 리뷰 재사용이
있을 수 있다. 결과 문장을 읽어 승인하면 이런 차이를 잃기 쉽다.

## 선택과 대안

| 방법 | 장점 | 한계 |
|---|---|---|
| AI에게 최종 승인까지 맡김 | 연결이 간단함 | 실행 여부·정책이 문장 판단에 묻힘 |
| 결정적 검사만 수행 | 재현성과 집계가 명확함 | 명세 누락·의미상의 문제는 놓칠 수 있음 |
| AI finding + 실행 검사 + 결정적 verdict | 두 종류의 근거를 보존함 | runner 진위·권한 격리를 별도로 구축해야 함 |

세 번째 구성을 시작했다. 코드는 verifier의 `src/godieor_verifier/engine.py`,
검사는 `tests/test_engine.py`에 있다. 기준은 현재 미승인 초안이다.

## 실제 확인한 것과 아직 못 한 것

- `scripts/self-test.sh`로 초기 엔진 검사 24개가 통과했다. 이후 수정 시 최신 결과는
  verifier의 `docs/bootstrap-validation.md`를 확인한다.
- 정상 evidence의 합성 테스트 외에, 비정상 종료 코드·필수 검사 누락·환경 오류·이전 SHA
  리뷰·AI 문장만 있는 결과가 PASS가 되지 않는지 확인했다.
- 예제 CLI는 실제 제품 실행을 하지 않는 가상 evidence다. 그 결과는 REVIEW_REQUIRED다.
- 자동 Git snapshot, 실제 test runner, 독립 AI 실행 어댑터, OS 권한 격리는 아직 구현 전이다.

자기 검사의 합성 승인 데이터는 메모리 안에서만 쓰며 사람의 승인이 아니다.
또 `isolation_verified: true`라는 문자열/값만으로 격리가 입증되는 것도 아니다.
판정 로직의 정확성과 evidence 자체의 진위는 서로 다른 검증 문제다.

## 학습 질문과 설명 초안

- 테스트가 모두 녹색이어도 PASS를 줄 수 없는 상황은 무엇인가?
- 저장소가 두 개면 실행 권한도 분리됐다고 할 수 있나?
- 리뷰가 지적을 내지 않았다는 사실과 제품이 맞다는 사실은 어떻게 다른가?

면접 설명 초안: ‘AI의 판단과 실행 근거를 나누는 검증기를 구성했고,
필수 검사 누락·오류·SHA 불일치를 차단하는 엔진을 먼저 검사했습니다.
실제 실행기와 보안 경계는 다음 단계라 시스템 전체가 완성됐다고 보지는 않았습니다.’
AI가 작성한 초안이며 사용자가 직접 설명했다는 기록은 아직 없다.
