# GODIEOR Verifier

[godieor-app](https://github.com/joobang/godieor-app)과
[godieor-backend](https://github.com/joobang/godieor-backend)의 독립 검증을 담당하는 저장소.
초기 구현은 **acceptance 초안 + AI 리뷰 계약 + 결정적 판정 엔진 + 엔진 자기 검사**다.
현재 런타임은 앱 전용 evidence v1이다. backend/계약/DB 조합 검증은 아직 구현하지 않았다.
외부 패키지·AI API·클라우드 DB 없이 Python 3.9 이상으로 실행한다.
verifier는 최종 구성에서도 Mac에서 필요할 때 실행한다. 제품 API/DB의 클라우드 운영과 별개다.

```sh
./scripts/self-test.sh
./scripts/verifier --acceptance requirements/acceptance.yaml \
  --evidence examples/evidence.json --out work/demo
```

두 번째 명령은 가상 evidence를 사용하는 데모다. 현재 기준은 draft이므로 `REVIEW_REQUIRED`와 종료 코드 2가 정상이다.
`work/demo/report.json`, `report.md`가 생성된다. 제품을 검사하거나 제품 PASS를 뜻하지 않는다.

| 종료 코드 | 판정 |
|---|---|
| 0 | PASS |
| 1 | FAIL |
| 2 | REVIEW_REQUIRED |
| 3 | ERROR |

## 문서

- [현재 상태·새 대화 시작점](docs/system/status.md) · [계정·모델 인계 절차](docs/system/handoff.md)
  (독립 제품 검토는 구현용 대화·웹 전달본을 상속하지 않음)
- [세 저장소 공통 설계](docs/system/architecture.md) · [작업 순서](docs/system/plan.md) · [정책 질문](docs/system/policies.md)
- [검증 저장소의 확장 작업](docs/repository-plan.md) · [acceptance 변경 제안](requirements/proposals/three-repositories.md)
- [실행 경계와 V1 구축 순서](docs/architecture.md)
- [기준 승인 절차](requirements/README.md)
- [독립 리뷰 프롬프트](prompts/independent-review.md)
- [evidence 입력 형식](docs/evidence.md)
- [wd-harness와 글에서 채택·제외한 원칙](docs/reference-adoption.md)
- [리뷰 지적 이력](reviews/README.md)
- [초기 구성 검사 결과](docs/bootstrap-validation.md)
- [통합 학습 카탈로그](docs/learning/README.md)

자동 Git snapshot·build/test runner·AI 호출 어댑터·OS 격리는 아직 없다.
판정 엔진은 **신뢰할 수 있는 실행기가 생성한 evidence**를 전제로 한다. 손으로 작성한 PASS나
`isolation_verified: true`는 실제 실행·격리의 증명이 아니다. 실행기를 완성하기 전 제품 승인에 사용하지 않는다.
