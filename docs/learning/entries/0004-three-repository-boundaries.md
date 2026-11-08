---
id: LEARN-0004
title: 앱·백엔드·검증 저장소의 책임과 버전 조합
kind: decision
status: draft
tags: [architecture, API-contract, verification, traceability]
created: 2026-11-09
updated: 2026-11-09
user_explanation: not-recorded
publication: private-draft
---

# 두 저장소에서 세 저장소로 바꿀 때 무엇을 함께 바꿔야 하나

실제 설계 변경 기록이다. 서비스 운영 장애나 통합 검증 완료 사례는 아니다.
사용자는 iOS 앱, backend, 독립 검증의 세 저장소를 요청했고 backend를 별도로 생성했다.
기존 app/verifier 문서는 앱 SHA만 기준으로 설계돼 있었으며 판정 코드도 그 상태다.

## 결정과 제안의 구분

- 사용자 확정: 저장소 세 개로 분리한다.
- 이번 설계 제안: backend가 정규화·DB·API 계약을, iOS가 소비·표시·기기 저장을 소유한다.
- 검증 설계 제안: 앱 SHA와 backend SHA, API 계약·DB migration·승인 기준을 한 조합으로 고정한다.
- 미확정: 스택·DB·로그인·세부 지역/플랫폼·갱신·AI 실행/권한 경계·배포 정책.

## 왜 버전 조합이 필요한가

iOS가 같은 SHA여도 backend API나 DB가 바뀌면 실제 동작은 바뀔 수 있다.
반대로 backend가 같아도 앱의 시간대 표시나 필터 요청이 바뀌면 사용자 결과가 달라질 수 있다.
그래서 부분 검사와 통합 검사를 구분하고, 이전 조합의 PASS를 새 조합에 재사용하지 않도록 설계한다.

## 대안과 비용

앱 레포 안에 backend를 두면 함께 변경하기는 쉽지만 이번 사용자가 원하는 저장소별 역할 분리가 약해진다.
세 저장소는 소유 범위를 드러내는 대신 API 계약·검증 대상·공통 문서의 동기화가 필요하다.
공통 문서는 한 원본과 revision을 둔 사본으로 관리하고, 코드/검사 기준의 소유 원본은 각 저장소에 둔다.
저장소 수가 늘어나는 것만으로 에이전트나 OS 권한이 분리되지는 않는다.

## 현재 결과와 한계

[공통 아키텍처](../../system/architecture.md), [작업 계획](../../system/plan.md),
[정책 질문](../../system/policies.md)을 세 저장소에 반영했다.
현재 evidence v1과 승인 전 acceptance는 유지했다. v2·runner·실제 DB/API는 다음 구현이다.
문서의 일치를 확인하는 것은 실행 환경의 독립성이나 제품 호환성을 증명하는 검사가 아니다.

## 스스로 설명할 질문

- 앱만 바뀌었을 때 backend 검사 결과를 어디까지 재사용할 수 있을까?
- API 계약의 원본을 backend에 둔 것과 backend 구현을 정답으로 삼는 것은 어떻게 다를까?
- 공통 문서 사본이 서로 달라지면 어느 내용을 기준으로 다시 맞춰야 할까?

면접·블로그에는 ‘역할과 계약을 정리한 설계 사례’로 설명한다.
실제 통합 검사나 운영 사례가 생기면 고정 버전 조합·실패/수정 근거를 추가한다.

## 후속 결정 이력 · 2026-11-09

초기 비교 이후 사용자가 NestJS + PostgreSQL + Prisma를 선택하고 TypeORM을 제외했다.
또한 최종 실행 위치를 본인 iPhone 앱 + 클라우드 API/DB, Mac verifier로 수락하고,
첫 목표를 로컬 API/DB와 앱의 연결로 정했다. 무료 우선 클라우드 제공자와 정확한 버전은 미정이다.
backend의 `docs/decisions/001-nestjs-postgresql.md`, `002-orm-options.md`, `003-runtime-topology.md`에
선택과 이전 제안을 구분해 기록했다. 로그인·동기화(P03)는 아직 결정 전이다.
이 변경은 설계/단계의 확정이며 실제 로컬 실행·원격 운영 완료를 뜻하지 않는다.

## 후속 계정·기록 위치 결정

2026-11-09 계정 기반 + Google 연동 방향을 반영했다. 계정 선택과 동기화 범위를 구분하고
backend ADR-004에 실행 흐름 제안을 기록했다. 실제 로그인 구현/OAuth 설정은 아직 없다.
이 통합 카탈로그는 app에서 verifier/docs/learning으로 옮겼고 각 저장소에는 원본 ADR/문제 기록을 남긴다.
학습·면접/블로그 해설은 원본과 독립 재현 근거를 연결한다.
