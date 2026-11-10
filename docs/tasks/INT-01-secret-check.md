# INT-01B · 비밀 검사와 iOS 흐름 후속
- 상태: 구현·작성자실행·독립재검토 완료. 담당해제.
- 기준: app594b080/verifier867c5b6/backendc5722cb. 요구사항 GD-010 및 GD-001/003/004/007의 UI 후속(초안).
- 범위: source/fixture/log/빌드bundle의 명시적 credential·민감정보 패턴 검사, 원문없는 결과·누락입력오류·실제runner연결. UI/설정검사는 별도실행범위 파악후 기록.
- 실패사례: 정상exit만PASS·누락bundle성공·symlink외부읽기·secret값로그노출·binary/plist누락·scanner오류성공·로컬설정유지를계정왕복으로위장.
- LEARN-ID: LEARN-0017 예정. 기준/승인상태 변경없음. 불특정개인정보/암호화·분할값부재의 수학적증명으로 주장하지 않음.

## 진행 기록
- scanner source/fixture/log/bundle 명시 literal 및 라벨PII 패턴, raw/UTF16/XML·binaryplist, 파일inventory/hash, path_id만 출력 구현.
- 독립review Hubble(01a1c306-8545-7b20-8011-990e1e33a2f4, fork_context=false)에서 rglob읽기오류누락/plist라벨소실/파일명이credential노출/root조상link/receiptbool타입 5건지적. os.walk onerror/구조보존JSON/path_id/조상검사/정확int로수정. fixture예외는전체파일hash로한정. 최종회귀확인중.
- 기존artifact로사전검사해템플릿2건·negativeURLfixture1건을탐지했고, 정확템플릿/고정파일hash예외로정리. 원문은결과·도구출력에복사하지않았다.

## 작성자 UI 수동 확인 (실제 backend 검증 아님)
- UI고정앱: /private/tmp/godieor-secret-7b4e5076/build/app/.../GODIEOR.app, 제품 iOS코드는app594b080의동일source. 대상 iPhone17/iOS26.5 Simulator A7DC0541-2B59-4A6E-9774-9E0B5F8C2D42.
- 별도가상계약server scripts/ui-contract-stub.py를loopback동적포트로실행하고 GODIEOR_API_BASE_URL 환경변수로연결. 실제provider/DB/서버동기화검사가아님.
- CUA:11/06 1건→검증용가상영화목록→상세 날짜만확인/예정/KR/가상데이터/출처 표시. 필터국가US·시간대UTC·netflixON→달력0건 및US/UTC표시.
- simctl terminate/launch로종료·재실행후 US/UTC/netflixON 복원, UI로확인. 마지막KR/AsiaSeoul/netflixOFF로복원후달력1건재표시확인.
- 서버request로그에서도필터query전달확인. 단순기기AppStorage복원을계정서버왕복이나전체UI검사PASS로승격하지않는다. settings-roundtrip/ios-user-flow는SKIPPED유지.

## 最终结果
- 修复后 scripts/self-test.sh 107项通过；独立reviewer也直接执行107项，并验证23种异常receipt均ERROR、文件/父目录名含synthetic token时FAIL且stdout/stderr/JSON不输出原值。全部5项发现已修复，再审无新增可复现问题。这里是代码审查，不是独立产品批准。
- 最后完整run /private/tmp/godieor-secret-05d7308f：iOS unsigned、backend47项、migration、API identity92/time76/filter57、DB smoke、secret-check全部exit0。scanner inventory182项（source和fixtures范围有交叉），finding0/error0，scope literal-credentials-and-labelled-pii。
- 输入app594b080/backendc5722cb，完整SHA见evidence；verifier867c5b6+当时dirty/state。source/contract/migration/acceptance及执行结果精确绑定，不把这次结果改称后续提交SHA的执行。
- 整体report仍ERROR：filter-intersection/settings-roundtrip/provider-contract/ios-user-flow四项SKIPPED；reviewPENDING、isolation_verified=false不变。操作性literal扫描PASS不表示所有个人信息/编码秘密绝对不存在。
- 产物保存在work/handoff/godieor-secret-05d7308f。UI请求记录work/handoff/ui-local-20261110。测试用server和Simulator app已停止，KR/AsiaSeoul/netflixOFF已复原；实际产品DB、Mac账号、ACL、钥匙串均未变更。
- LEARN-0017。任务实现/作者执行/独立代码再审完成，担当解除。下一步应推进Google/账号设置或真实提供方数据，UI/设置尚未实现的服务端功能不能仅靠重复模拟UI检查“验证完成”。
