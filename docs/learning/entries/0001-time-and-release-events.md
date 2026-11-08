---
id: LEARN-0001
title: 날짜와 시각, 콘텐츠와 공개 이벤트의 분리
kind: decision
status: draft
tags: [time, data-model, iOS, API]
created: 2026-11-06
updated: 2026-11-06
requirements: [GD-005, GD-006, GD-007, GD-009]
user_explanation: not-recorded
publication: private-draft
---

# 날짜와 시각, 콘텐츠와 공개 이벤트를 왜 나누는가

이 기록은 **예방적 설계 사례**다. 실제 서비스에서 날짜 오류가 발생했다는 경험담이 아니다.
현재 앱은 시작 화면 단계이며 아래 데이터 모델과 동작은 아직 구현하지 않았다.

한 작품은 한국 극장, 한국 OTT, 다른 지역 공개, 회차별 공개라는 여러 일정을 가진다.
작품 ID 하나에 공개 날짜 하나만 저장하면 서로 다른 이벤트를 잃을 수 있다.
또 ‘날짜를 안다’와 ‘UTC 시각을 안다’는 정보의 양이 다르다.

## 사실과 가설

| 구분 | 내용 | 근거/확인 상태 |
|---|---|---|
| 공식 문서 사실 | TMDB 영화 공개 유형에 극장과 digital 구분이 있다 | [공개일 문서](https://developer.themoviedb.org/reference/movie-release-dates), 2026-11-06 조회 |
| 공식 문서 사실 | watch providers는 국가별 플랫폼 가용성을 제공한다 | [플랫폼 문서](https://developer.themoviedb.org/reference/tv-series-watch-providers), 2026-11-06 조회 |
| 설계 판단 | 콘텐츠 ID와 공개 이벤트 ID를 나누고 날짜 정밀도를 보존한다 | [제품 요구사항](https://github.com/joobang/godieor-app/blob/dev/docs/product.md), acceptance GD-005~007 초안 |
| 아직 미검증 | 실제 각 API 응답을 정규화했을 때의 한국 일정 정확도 | 실제 API 호출 전 |

## 예제로 이해하기

`2026-11-06T20:00:00Z`라는 **가상 시각**은 KST에서 다음 날 05:00이다.
하지만 한국 공개일 `2026-11-06`이라는 날짜만 있는 정보에는 그 변환을 적용할 UTC 시각이 없다.
이를 임의로 자정으로 바꾸면 원본에 없던 사실을 만든다.

‘Netflix에서 시청 가능’이라는 정보도 ‘한국 Netflix에서 이날 공개’라는 정보와 구분해야 한다.
데이터 모델은 편리한 표시보다 원본이 실제로 아는 범위를 보존해야 한다.

## 대안과 선택

| 방법 | 이점 | 이 경우의 문제 |
|---|---|---|
| 작품 하나에 대표 날짜 하나 | 구현이 단순함 | 지역·회차·극장/OTT 차이를 잃음 |
| 모든 날짜를 UTC timestamp로 통일 | 정렬·형식이 단순함 | 날짜만/미정 정보에 가짜 시각을 만들 수 있음 |
| 콘텐츠/이벤트 분리 + instant/date_only/unknown | 의미와 출처를 보존함 | 정렬·중복·UI 처리가 더 필요함 |

세 번째 방법을 제안한다. 세부 API 계약과 중복 병합 규칙은 독립 검사 기준 승인 이후 확정한다.
검증 계획은 지역별 분리, 회차 분리, 날짜 rollover, DST, date-only 불변, TBD 날짜 없음이다.

## 스스로 답할 질문

- timestamp 필드가 있다고 실제 공개 시각까지 안다고 말할 수 있을까?
- 같은 작품이 두 플랫폼에 나오면 언제 합쳐도 될까?
- 일정이 연기됐을 때 ID를 바꾸면 어떤 중복이 생길까?

면접·블로그에서는 ‘설계 중 발견한 데이터 의미 문제’로 설명한다.
구현·실제 연동 후 run ID와 실패/수정 사례를 보강하기 전에는 해결 성과로 쓰지 않는다.
