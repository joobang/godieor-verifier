# OTT 후보 코드 검토 · 2026-11-09

검토 대상: backend base b0c7f258f3041776de20cc55afc5ea5f164c9e05 + 당시 미커밋 후보 구현.
새 컨텍스트 reviewer: Aquinas / agent 01a1be7e-22f3-7a32-a907-ca171c2276e8.
구현 대화·작업 카드·학습 기록을 전달하지 않고 요구사항, base SHA, 대상 파일/검토 범위만 제공했다.
작성자가 아래 결과를 기록한다. 승인 acceptance/verdict나 세 저장소 통합 PASS를 생성하지 않는다.
OS 권한 격리·실제 네트워크 수집 검증을 이 코드 리뷰가 증명하지 않는다.

## 최초 리뷰에서 재현한 지적

- P2 / OTT-REV-01: 변경본 등록 후 state.review는 해제되지만 기존 reviewed.json이 남아 무효 검토를 후속 입력으로 사용할 수 있음.
- P2 / OTT-REV-02: A→B→A로 되돌아오면 내용 hash가 같아져 최초 A 검토 JSON을 다시 적용할 수 있음.
- reviewer는 지정 Node24에서 임시 컴파일·기존 14검사와 두 반례를 재현했고 저장소를 수정하지 않았다고 보고함.

## 구현 담당 수정

- mutation 시작 시 기존 reviewed.json을 삭제해 재생성 전 사용을 막음. list/export는 읽기/내보내기 경로로 구분.
- 내용 hash와 revision 발생 token을 분리. token에 후보 ID와 발생 회차를 포함해 A→B→A에서 이전 검토를 거부.
- 회귀 검사 추가 후 작성자 최종 15개 자체 검사 통과. 이번 세션이 만든 ignored v1 후보 이력을 v2로 옮기고 기존 검토를 해제·재확인함.

## 재확인 대상 파일 SHA-256

- `src/candidates.ts`: `d6fad89466466622e338e04d9b9e5fefffbba8cafc5f5ceaccfef5e42238e422`
- `src/collect-candidates.ts`: `e2a0bdde36300c7a165ea989478d2092d3ff2f09df7b45fa81835d9f805f2bef`
- `tests/candidates.test.cjs`: `42f5b1ff4291dceaa460f8b5e85e1635a25756b261d299a9cfb69ca1d25b4755`
- `package.json`: `5b6c38426d829ee4f5ba573c3fc75ac3b17b77f7d53c84226ee0afd9699b7cb1`
- `package-lock.json`: `c1ff417af46bd1328e890dadb094130837fbe8dd41b4ac8699ef6da54ca15246`

## 1차 재확인

reviewer가 기존 두 경로의 수정(A→B→A 옛 입력 STALE_REVIEW, mutation 후 파일 삭제, list 파일 보존)을 재현 확인했다.
추가 P2 / OTT-REV-03: v1 상태에서 모든 CLI가 실패하고 mutation은 export 선삭제하므로 승계 경로가 필요함.

구현 담당은 legacy v1 검증·후보/이력 보존 변환·review 해제, readState 성공 뒤 export 무효화,
미지원/손상 상태 파일 보존을 구현했다. 작성자 최종 빌드/17개 검사 통과.

## 최종 재확인 대상 SHA-256

- `src/candidates.ts`: `b0b59072bceeef0bc7fc3c38264a4a9f41564968c504c9ea5ed856f3fdad4c11`
- `src/collect-candidates.ts`: `e2a0bdde36300c7a165ea989478d2092d3ff2f09df7b45fa81835d9f805f2bef`
- `tests/candidates.test.cjs`: `31241bdf2922c63c3fc0fe56e088b233b1c583b09ba6ed9c701bd74d441d39c2`
- `package.json`: `5b6c38426d829ee4f5ba573c3fc75ac3b17b77f7d53c84226ee0afd9699b7cb1`
- `package-lock.json`: `c1ff417af46bd1328e890dadb094130837fbe8dd41b4ac8699ef6da54ca15246`

## 최종 별도 재확인 수신

reviewer는 요청한 재검토 범위에서 추가 결함을 발견하지 못했다고 보고했다.
A→B→A 옛 검토 거부, mutation export 삭제/v2 list 보존, v1 후보·3 revision 이력 보존/검토 해제/변환 저장,
미지원 버전·깨진 JSON·잘못된 후보 ID의 상태/export 보존을 별도 CLI로 재현 확인했다.
Node24 임시 컴파일·17개 검사도 통과했다고 보고했다. 실제 RSS·전체 Prisma 빌드는 수행하지 않았다고 명시했다.

이 기록은 위 hash의 코드 검토 재확인 결과다. 고정 Git snapshot/승인 acceptance에 의한 제품 DB/API/iOS 통합 검증은 범위 밖이다.
구현 담당은 이 결과를 세 저장소 통합 PASS나 제품 승인으로 표시하지 않는다.
