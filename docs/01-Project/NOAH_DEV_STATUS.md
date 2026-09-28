# NOAH 개발 현황

> 기준일: 2026-09-29 (Asia/Seoul)
> 성격: 구현·검증 진행 상황의 요약. 기존 Blueprint와 Accepted DDR을 대체하거나 변경하지 않는다.
> 첫 Slice 기준 커밋: `061dbea` — 인증된 PostgreSQL 메모 저장 구현. 이후 반영 상태는 Git 기록을 따른다.

## 현재 마일스톤

**구현 완료 기준선 — M8 단일 문서 근거 인용형 질문 응답:** M7 방식으로 검증한 승인 프로젝트의 `.md` 한 건을 제한된 로컬 모델 Context로 사용한다. 모델의 구조화된 인용 후보를 NOAH가 원문과 대조하고 답변을 조립한다. M8까지 GitHub `main`에 반영된 기준 커밋은 `c0c97ffd6322884e4ae3fa18ff8e8c9105b0cde5`이다. 실제 사용자 문서는 모델에 전달하지 않았고, 합성 프로젝트로 Compose PostgreSQL 17에서 자동 및 수동 검증했다. 범위와 제한은 [M8 계약](27-Eighth-Vertical-Slice.md), 실행 결과는 [M8 검증 기록](28-Eighth-Slice-Validation.md)을 따른다.

**현재 구현 — M9 두 문서 근거 응답:** 같은 프로젝트에서 사용자가 직접 지정한 서로 다른 `.md` 두 건과 질문 하나를 처리한다. M7 안전 읽기와 파일 identity 대조를 거친 뒤 로컬 모델의 출처별 인용 후보를 NOAH가 검증한다. 독립 Task·Execution 및 M9 전용 Evidence를 기록한다. 구현 범위는 [M9 계약](29-Ninth-Vertical-Slice.md), 자동 테스트와 별도 사용자 수동 API 검증은 [M9 검증 기록](30-Ninth-Slice-Validation.md)을 따른다. M9 변경은 현재 최종 검토 전 작업 트리에 있으며 아직 커밋·Push하지 않았다.

## 완료된 기능과 구현 범위

- 로컬 HTTP `POST /memories`: 명시적 `save_memory` 요청만 처리한다.
- PostgreSQL에 저장한 해시로 bearer token을 인증하고, 개인 메모의 소유자 또는 프로젝트 쓰기 권한을 확인한다.
- 입력 및 저장 범위를 검증하고, 메모를 PostgreSQL에 저장한 뒤 DB에서 재조회해 결과를 확인한다.
- 선택적 `Idempotency-Key`를 사용자별로 PostgreSQL에 예약한다. 같은 요청의 성공 재시도는 기존 메모·Task·실행 ID를 돌려주고, 다른 요청 내용이면 충돌을 반환한다. 동시 요청과 서버 프로세스 재시작 후에도 중복 저장을 막는다. 키 없는 기존 API 동작은 유지한다.
- Task의 지속 상태와 실행 기록을 별도 테이블에 남긴다. 성공에는 메모 ID와 재조회 증거를, 거부·실패에는 구조화된 실패 코드를 반환한다.
- `python -m noah recovery-report`는 Memory Write 영속 기록을 읽기 전용 스냅샷에서 점검한다. 검증 완료, 기록된 실패, 미종결 running, 기록 불일치를 분류하며 불확실한 결과는 실패로 단정하거나 재실행하지 않는다. 인증정보와 메모 본문은 보고하지 않는다.
- `GET /memories/<id>`는 같은 범위 권한으로 저장된 메모를 조회한다.
- `GET /memories`는 인증된 사용자가 읽을 수 있는 개인·프로젝트 메모만 반환한다. 프로젝트 소속 사용자는 쓰기 권한이 없어도 읽을 수 있다. 생성 시각과 ID의 역순 정렬 및 커서 페이지네이션을 제공한다.
- `POST /memories/query`는 토큰 인증 후 로컬 Ollama가 제안한 읽기 의도와 질문의 단어를 검증한다. 기존 개인·프로젝트 조회 권한 필터를 공유하는 매개변수화 검색으로 최대 5건을 조회하고, 제한된 본문을 모델에 전달한다. 답변에는 실제 조회 결과의 ID와 원문이 일치하는 발췌만 사용한다. 빈 결과·근거 부족·검색 한도와 DB/모델 오류를 구분한다.
- `POST /projects/<project_id>/documents/query`는 모델이 제안한 제한된 읽기 의도를 NOAH가 재검증하고, 실행 직전 프로젝트 소속을 재확인한다. 운영자만 관리하는 Git 제외 로컬 mapping의 문서 루트에서 직접 하위 일반 `.md` 파일명 최대 50개를 읽어 검증한다. Task·Execution 및 별도 Tool Evidence에 결과를 연결하고 본문이나 절대경로를 모델·API에 보내지 않는다.
- `POST /projects/<project_id>/documents/read`는 정확한 `.md` 파일명 하나를 받아 권한을 재검사하고, Windows에서는 reparse point를 따라가지 않는 파일 핸들로 최대 65,536 원본 바이트를 읽는다. strict UTF-8/BOM을 검증하고 독립 재조회와 SHA-256을 대조한 뒤 별도 Document Evidence와 Task·Execution을 함께 확정한다. 본문은 API의 인증된 요청자에게만 반환하며 LLM에는 전달하지 않는다.
- `POST /projects/<project_id>/documents/answer`는 인증·프로젝트 읽기 권한·단일 문서명·질문을 검증한다. M7 내부 safe-read와 원본 hash 검증을 재사용하고 2,048 UTF-8 byte 이하의 본문을 별도 로컬 모델에 untrusted data로 전달한다. 모델은 outcome과 최대 3개 exact quote만 제안하며, NOAH가 240 Unicode 문자 이하 인용을 원문에 대조하고 첫 `[start,end)` 위치를 계산한다. 하나의 M8 Task/Execution에 문서 관찰 Evidence와 답변 Evidence를 원자적으로 연결한다. 추가 Tool과 자유 형식 모델 답변은 사용하지 않는다.
- `POST /projects/<project_id>/documents/answer-selected`는 사용자가 지정한 서로 다른 직접 하위 `.md` 정확히 두 건을 D1/D2 순서로 읽는다. Windows에서는 no-follow 핸들의 volume/file index, POSIX에서는 device/inode로 동일 실제 파일을 차단한다. 두 본문 합계 최대 2,048 UTF-8 bytes와 system/user 메시지 본문 합계 최대 3,456 bytes를 적용한다. 모델은 기존 다섯 outcome과 최대 3개의 `{source_id, quote}`만 제안하고, NOAH가 해당 문서의 원문과 위치를 대조한다. 하나의 M9 Task/Execution에 별도 부모·문서별 관찰·인용 Evidence를 원자적으로 연결한다. 다른 문서 자동 탐색, 추가 Tool, 자유 형식 답변은 없다.
- 기존 `compose/.env`와 Docker Compose PostgreSQL 설정을 사용한다. 로컬 운영 명령으로 스키마 초기화, 사용자 토큰 발급 및 프로젝트 생성을 지원한다.

구현 위치: [`noah/`](../../noah/), [`database/001_first_slice.sql`](../../database/001_first_slice.sql), [`database/002_memory_write_idempotency.sql`](../../database/002_memory_write_idempotency.sql), [`database/003_document_tool_evidence.sql`](../../database/003_document_tool_evidence.sql), [`database/004_document_read_evidence.sql`](../../database/004_document_read_evidence.sql), [`database/005_document_answer_evidence.sql`](../../database/005_document_answer_evidence.sql), [`database/006_selected_document_answer_evidence.sql`](../../database/006_selected_document_answer_evidence.sql), [`tests/`](../../tests/). 실행 절차: [First vertical slice](13-First-Vertical-Slice.md), [Second vertical slice](15-Second-Vertical-Slice.md), [Third vertical slice](17-Third-Vertical-Slice.md), [Fourth vertical slice](19-Fourth-Vertical-Slice.md), [M5 read-only triage](21-Fifth-Vertical-Slice.md), [M6 Tool Execution](23-Sixth-Vertical-Slice.md), [M7 Document Read](25-Seventh-Vertical-Slice.md), [M8 Document Answer](27-Eighth-Vertical-Slice.md), [M9 Selected Answer](29-Ninth-Vertical-Slice.md). M2·M3·M5에는 DB 스키마 변경이 없었고, M4·M6·M7·M8·M9은 기존 데이터를 유지하는 추가 테이블을 마이그레이션했다.

## 테스트 및 검증

| 환경 | 마지막 실행 | 결과 | 범위 |
| --- | --- | --- | --- |
| 격리 PostgreSQL 18 | 2026-09-24 | 5개 통과, 실패·오류·건너뜀 0개 | DB 통합 테스트 4개와 의도적인 DB 연결 실패 테스트 1개 |
| 기존 Docker Compose PostgreSQL 17 | 2026-09-25 | 5개 통과, 실패·오류·건너뜀 0개 | DB 통합 테스트 4개와 의도적인 DB 연결 실패 테스트 1개 |
| 기존 Docker Compose PostgreSQL 17 — M2 | 2026-09-27 | 메모 목록 테스트 7개와 M1 회귀 테스트 4개 통과, 실패·오류·건너뜀 0개 | 실제 DB의 권한 필터, 빈 목록, 정렬·페이지네이션, HTTP 조회, 메모 저장·롤백 회귀 |
| 기존 Docker Compose PostgreSQL 17 + 로컬 Ollama — M3 | 2026-09-28 | 전체 24개 재실행 통과, 실패·오류·건너뜀 0개 | 합성 사용자·메모의 인증, 개인·프로젝트 권한, 근거 검증, 모델·DB 오류, Write/Read 회귀 |
| 기존 Docker Compose PostgreSQL 17 + 로컬 Ollama — M4 | 2026-09-28 | 전용 테스트 6개 및 전체 30개 통과, 실패·오류·건너뜀 0개 | 키 재시도·충돌·동시성·롤백·커밋 응답 유실·실제 서버 프로세스 재시작, M1–M3 회귀와 합성 메모의 실제 Ollama 호출 |
| 기존 Docker Compose PostgreSQL 17 — M5 | 2026-09-28 | M5 전용 2개 통과; 전체 32개 중 31개 통과·1개 건너뜀, 실패·오류 0개 | 합성 Task·Execution·Memory·매핑 분류와 진단 전후 불변성, M1–M4 회귀. 건너뜀은 명시적 실제 Ollama 호출 테스트 |
| 기존 Docker Compose PostgreSQL 17.10 + 로컬 Ollama — M6 | 2026-09-28 | 최초 M6 16개·전체 48개 통과; PowerShell 5.1 호환성 보완 후 M6 18개·전체 50개 통과, 실패·오류·건너뜀 0개 | 합성 프로젝트·임시 문서 루트의 인증·권한 재검사·경로 필터·근거·실패 계약, UTF-8 BOM 유무 및 잘못된 mapping 처리, M1–M5 회귀 |
| 기존 Docker Compose PostgreSQL 17 + 로컬 Ollama — M7 | 2026-09-28 | M7 전용 13개·전체 63개 통과, 실패·오류·건너뜀 0개 | 합성 사용자·프로젝트·문서 루트의 제한된 본문 읽기, Windows 실제 junction 차단, 원본 바이트 근거, Task/Execution/Evidence, M1–M6 회귀 및 실제 합성 Ollama 호출 |
| 기존 Docker Compose PostgreSQL 17 + 로컬 Ollama — M8 | 2026-09-29 | M1–M8 전체 79개 통과, 실패·오류·건너뜀 0개 | 합성 프로젝트·문서의 한정된 모델 Context, exact quote 검증, 권한 재검사, 원자적 Evidence, 실제 합성 Ollama 호출 및 M1–M7 회귀 |
| 기존 Docker Compose PostgreSQL 17 + 로컬 Ollama — M9 | 2026-09-29 | M1–M9 전체 93개 중 91개 통과·2개 건너뜀, 실패·오류 0개; 건너뛴 M3/M6 실제 Ollama 2개는 별도 실행 통과 | M9 전용 14개 중 실제 모델 포함 14개 통과, 출처별 인용·파일 identity·권한 회수·원자적 Evidence 및 M1–M8 회귀. M3/M6 opt-in 환경변수는 별도로 설정해 실행 |

M1 Compose 테스트는 실제 외래 키 위반에 따른 메모 쓰기 롤백과 실패 Task·실행 기록을 확인했다. M1의 재시작 검증은 HTTP 서버 인스턴스를 **같은 Python 프로세스에서** 종료·재생성한 것이고, M4는 별도 테스트에서 NOAH Python 서버 **프로세스 자체를** 종료·재시작한 뒤 동일 키 재요청을 확인했다. 자동 테스트용 행은 정리했다. 초기 7개 테이블에 M4 1개, M6 1개, M7 1개, M8 1개, M9 Evidence 3개가 추가되어, **현재 `noah` 스키마는 14개 테이블**이다. M6–M9 합성 검증 정리 후 관련 Evidence 테이블의 행은 각각 0건이지만 테이블은 유지된다. 기존 Compose 컨테이너와 named volume은 테스트 전후 동일한 것으로 확인했다.

M1 상세 근거와 실패 주입 기록: [First Slice Validation Record](14-First-Slice-Validation.md). M2 검증 및 기존 사용자 데이터 보존 결과: [Second Slice Validation Record](16-Second-Slice-Validation.md). M3 모델 비교, 안전한 로컬 리스너, 실제 Compose·Ollama 검증: [Third Slice Validation Record](18-Third-Slice-Validation.md). M4의 마이그레이션, 동시 요청, 실제 서버 프로세스 재시작과 M1–M3 회귀 검증: [Fourth Slice Validation Record](20-Fourth-Slice-Validation.md).

2026-09-28 사용자 수동 검증에서는 NOAH 전용 Ollama의 루프백 리스너와 모델 등록, 인증 거부 동작을 확인했다. 기존 개인 메모에 대한 자연어 질문은 `succeeded/grounded`, `scope=all`, `examined=1`, `truncated=false`로 응답했고, 사용자는 근거 ID와 원문 발췌를 확인했다. 개인 메모 원문과 인증정보는 [M3 검증 기록](18-Third-Slice-Validation.md)에 넣지 않았다.

M4의 **별도 사용자 수동 검증**에서 공개용 테스트 메모의 첫 저장은 HTTP 201, 동일 키·동일 본문 재요청은 HTTP 200과 `replayed: true`였으며 memory_id·task_id·execution_id가 모두 같았다. 동일 키에 다른 내용을 보낸 요청은 HTTP 409와 `IDEMPOTENCY_CONFLICT`였다. 읽기 전용 DB 확인 결과, 수동 테스트 전→후 사용자 **1→1**, 활성 토큰 **1→1**, 개인 메모 **1→2**, Task **1→2**, Execution Record **1→3**, 키 매핑 **0→1**이었다. 재요청은 새 메모·Task·Execution Record를 만들지 않았고, 충돌은 메모나 Task 없이 실패 Execution Record 한 건만 남겼다. 기존 사용자·토큰·이전 개인 메모는 유지되며 `running` Task와 Execution Record는 각각 0건이다. 자세한 참조 관계는 [M4 검증 기록](20-Fourth-Slice-Validation.md)에 보존했다.

M5에서는 합성 자료로 완료·확정 실패·예약 후 미종결·응답 유실·상태/참조 불일치·DB 연결 실패를 점검했다. 진단 전후 합성 Task·Execution·Memory·매핑 행이 동일했으며 테스트 소유 행만 정리했다. 기존 DB의 별도 읽기 전용 진단 결과는 검증 완료 2건, 기록된 실패 1건, 미종결 및 불일치 0건이었다. 정확한 시험 범위와 실제 Ollama 호출 건너뜀은 [M5 검증 기록](22-Fifth-Slice-Validation.md)에 남겼다.

M5의 **별도 사용자 수동 검증**에서도 `recovery-report`가 `succeeded`, 검사 3건, 검증 완료 2건, 기록된 실패 1건을 반환했다. 미종결 running 및 기록 불일치는 보고되지 않았고 세 항목 모두 `issues: []`였다. 완료된 두 항목은 `completed/succeeded/passed`와 검증 시각·메모 참조·실제 메모 존재를 표시했다. 한 항목에만 키 매핑이 있는 것은 기존 무키 저장과 M4 이후 키 저장 이력에 부합하지만, 매핑 유무만으로 생성 시기를 증명하지는 않는다. 수동 관찰의 자세한 내용은 [M5 검증 기록](22-Fifth-Slice-Validation.md)에 자동 테스트와 구분하여 남겼다.

M6 합성 검증에서는 실제 사용자 데이터와 분리된 프로젝트·membership·임시 문서 루트로 HTTP 경로, 제한된 실제 Ollama 의도, 파일명 검증, Task/Execution/Evidence 연결을 확인했다. 테스트 소유 행 정리 뒤 사용자 1명·토큰 1건·개인 메모 2건·Task 2건·Execution 3건·M4 키 매핑 1건은 유지됐고 프로젝트·membership·M6 evidence는 0건이었다. 자세한 제한과 테스트 결과는 [M6 검증 기록](24-Sixth-Slice-Validation.md)에 있다.

M6의 **별도 사용자 수동 검증**에서는 Windows PowerShell 5.1의 `application/json` 요청에서 한국어가 손상되어 `UNSUPPORTED_INTENT`가 반환됐다. `charset=utf-8`을 지정하자 같은 한국어 질문의 intent가 통과했다. BOM이 든 local mapping에서는 `PROJECT_ROOT_CONFIG_INVALID`였고, BOM 없는 mapping으로 다시 저장한 뒤 `project.documents.list`가 성공했다. 응답에는 합성 `alpha.md`, `beta.md`, `gamma.md`만 있었고 비 `.md` 파일, 본문, 절대경로는 없었다. 사용자는 Task·Execution·Tool Evidence 및 hash를 확인하고 임시 행·mapping·문서 루트를 정리했다. 별도 읽기 전용 확인에서 기존 사용자 1·토큰 1·메모 2·Task 2·Execution 3·M4 매핑 1, 프로젝트·membership·M6 evidence·running 기록 0건이었다. 실행 안내의 UTF-8 전송·BOM 없는 저장 예시와 BOM 유무를 허용하는 로더를 보완했다. 수동 결과와 자동 테스트는 [M6 검증 기록](24-Sixth-Slice-Validation.md)에 구분해 남겼다.

M7 자동 합성 검증은 인증·권한 재검사·문서명과 파일 유형·원본 바이트 크기·strict UTF-8/BOM·근거 hash·상태 연결을 확인했다. 기존 사용자·토큰·메모·Task·Execution·M4 매핑 수는 테스트 전후 동일했고 M7 evidence 행은 정리 후 0건이었다.

M7의 **별도 사용자 수동 검증**에서 실제 서버/API의 단일 `.md` 읽기는 본문·UTF-8·원본 byte length·SHA-256 대조를 통과했고 절대경로를 노출하지 않았다. 성공 요청에는 Task·Execution·Document Read Evidence가 각각 정확히 1건 연결됐으며 Evidence에는 본문 전체나 절대경로가 없었다. 기존 Memory와 M6 Evidence는 변하지 않았다. `../<document>` 요청은 HTTP 400 `INVALID_DOCUMENT_IDENTIFIER`와 null Task/Execution ID로 거부됐고 전후 DB snapshot이 같았다. 합성 프로젝트·membership·M7 실행 기록·문서 루트·local mapping만 정리한 뒤 기존 행 수·ID와 토큰/메모/M4 지문이 사전 상태로 복원됐다. Windows PowerShell 5.1에서 실패 응답의 `GetResponseStream()`은 빈 본문을 주었지만 `$_.ErrorDetails.Message | ConvertFrom-Json`으로 오류 코드를 확인했다. 자동 테스트와 수동 검증의 상세 결과는 [M7 검증 기록](26-Seventh-Slice-Validation.md)에 구분해 남겼다.

M8은 합성 한국어·영어 문서로 현재 로컬 모델의 Context 응답을 확인하고, Docker Compose PostgreSQL 17에서 단일 문서 질문·인용 검증·권한 회수·원자적 기록 및 전체 M1–M7 회귀를 검증했다. 기존 사용자 1·토큰 1·메모 2·Task 2·Execution 3·M4 매핑 1을 유지하고, 합성 project/membership 및 M6–M8 Evidence는 정리 후 각각 0건이다. 실제 개인 문서에 대한 수동 M8 검증은 수행하지 않았으며 공개 합성 문서로 수동 API 검증했다. 세부 결과와 제한은 [M8 검증 기록](28-Eighth-Slice-Validation.md)에 있다.

M8의 **별도 사용자 수동 API 검증**에서는 공개 합성 `.md`에 대한 성공 요청 1회가 HTTP 200, `succeeded`, `project.documents.answer`, `supported`, `grounded=true`를 반환했다. `NOAH의 테스트 동물은 수달이다.` 인용은 원문과 정확히 일치했고 NOAH가 계산한 `[start,end)` 위치도 일치했다. Task·Execution·문서 관찰 Evidence·답변 Evidence가 연결됐으며 추가 `project.*` Execution이나 M6 Tool Evidence는 없었다. `../document`는 HTTP 400 `INVALID_DOCUMENT_IDENTIFIER`와 null Task/Execution으로 거부됐고 전후 DB snapshot이 같았다. 합성 행·mapping·임시 문서 root를 정리한 뒤 `MappingExists=False`, `RootExists=False`, `DbRestored=True`를 확인했다. PowerShell 5.1에서 단일 Evidence 객체에 대한 파이프라인 `.Count`는 false negative였으므로 수동 안내는 `@(...)` 배열 감싸기로 바로잡았다. 자동 검증과 구분한 근거는 [M8 검증 기록](28-Eighth-Slice-Validation.md)에 있다.

M9의 **자동 합성 검증**에서는 같은 프로젝트의 두 `.md`를 D1/D2 순서로 안전하게 읽고 실제 파일 identity가 같은 hard link를 차단했다. Docker Compose PostgreSQL 17에서 출처별 exact quote, 다섯 outcome, 권한 회수, 오류·원자적 기록, 기존 M1–M8 회귀를 확인했다. 실제 전용 Ollama에 한국어/한국어·영어/영어·혼합 문서 합계 1,809–1,830 bytes를 보냈고 모두 두 출처의 검증된 인용을 반환했다. 별도 영어 합성 입력 2,048 bytes의 전체 프롬프트는 3,153 bytes였고 정상 검증됐다. 테스트 전후 기존 사용자 1·토큰 1·메모 2·Task 2·Execution 3·M4 매핑 1의 수와 지문이 같고, project·membership·M6–M9 Evidence·running 기록은 0건이다. 자세한 범위와 2건의 opt-in 건너뜀 및 별도 통과 결과는 [M9 검증 기록](30-Ninth-Slice-Validation.md)에 기록했다.

M9의 **별도 사용자 수동 API 검증**에서는 공개 합성 문서 두 건에 성공 요청을 정확히 1회 보냈고 HTTP 200, `succeeded`, `project.documents.answer.selected`, `grounded=true`를 확인했다. `수달` 인용은 D1, `파란색` 인용은 D2의 실제 원문·Unicode `[start,end)` 위치에 정확히 연결됐다. 하나의 M9 Task/Execution과 answer parent·D1/D2 observation·quote Evidence가 연결됐고 추가 M7/M8 Execution이나 legacy Evidence는 없었다. 응답/Evidence에 절대경로·인증정보·전체 문서 본문이 없음을 확인했다. 동일 문서명을 두 번 지정한 요청은 HTTP 400 `DUPLICATE_DOCUMENT_NAME`, null Task/Execution으로 거부됐고 DB snapshot은 변하지 않았다. 합성 행과 local mapping·두 파일·root 정리 후 기존 DB의 행 수·ID·비공개 지문이 사전 snapshot과 동일했다. PowerShell 5.1의 multiline Python `-c` 전달 오류와 cleanup 예시의 존재하지 않는 `document_answer_evidence.project_id` 조회는 수동 절차 문제였다. stdin 전달 및 해당 M9 `execution_id` 기준 legacy Evidence 조회로 바로잡은 후 정리가 완료됐다. 자세한 자동/수동 구분은 [M9 검증 기록](30-Ninth-Slice-Validation.md)에 남겼다.

## 알려진 제한 사항

- 메모 쓰기 멱등성은 새 요청의 선택적 키에만 적용된다. 키 없는 과거·현재 쓰기는 재시도로 중복될 수 있고, 확정 실패를 같은 키로 자동 재실행하지 않는다. 커밋 결과가 불확실할 때는 같은 키로 내구 상태를 재조회할 수 있으나 자동 복구는 없다.
- DB 연결이 실행 중 끊어지면 로컬 실패 기록은 남길 수 있지만, DB에 남은 `running` Task를 자동으로 복구·정리하는 기능은 없다.
- M5 진단은 현재 `memory.save`에 한정된다. `running`에서 Runtime 생존 여부나 최종 커밋 가능성을 판단할 지속적 소유권·fencing 근거가 없으므로 자동 상태 전이와 쓰기 재실행을 하지 않는다. Task의 현행 goal 문자열로 범위를 식별하므로 향후 일반화에는 명시적 capability 연계가 필요하다.
- M6의 프로젝트→문서 루트 mapping은 운영자 로컬 설정에서만 제공한다. 현재 실제 프로젝트와 membership이 각각 0건이므로 운영자가 범위를 등록하기 전에는 실제 사용자 대상 Tool 조회를 할 수 없다. M6 결과는 조회 시점의 파일명 관찰이며 파일 내용·후속 변경을 보증하지 않는다.
- M6 경로 보장은 사용자·모델·원격 입력을 통한 탈출에 초점을 둔다. 동일 Windows 사용자 권한의 악성 로컬 프로세스가 검사와 열거 사이에 링크를 바꾸는 공격까지 보장하지 않는다. Windows 테스트 계정에서 실제 symlink 생성은 허용되지 않아 해당 제외 분기는 합성 reparse 속성으로 시험했다.
- M7은 파일 본문을 검증된 관찰로 반환하지만 요약하거나 Knowledge로 적재하지 않는다. 실제 symlink 생성이 허용되지 않아 합성 reparse 분기와 실제 junction 거부를 검증했다. 동일 Windows 사용자의 악성 로컬 경로 교체 경쟁은 보장 범위 밖이다.
- M8은 선택된 단일 문서의 실제 인용과 위치만 검증한다. 인용의 현실 세계 사실성이나 질문과의 완전한 의미적 적합성은 증명하지 않는다. 2,048 UTF-8 byte Context 초과 문서는 실패하며 자동 분할·요약하지 않는다. M5 Recovery Triage는 M8 실행을 복구하지 않는다.
- M9의 `grounded` 역시 D1/D2 원문 인용·위치·관찰 hash의 연결만 검증한다. 두 인용이 질문에 의미상 충분하거나 현실 세계에서 참인지는 증명하지 않는다. 두 문서 합계 2,048 UTF-8 bytes 또는 전체 프롬프트 3,456 bytes 초과는 조용히 자르지 않고 거부한다. 순차 관찰은 단일 파일시스템 snapshot이 아니며, M5는 M9을 복구하지 않는다.
- HTTP API는 로컬호스트에만 바인딩한다. 원격 배포용 TLS, 운영 인증·권한 관리, 속도 제한은 범위 밖이다.
- `noah init`은 첫 스키마와 M4·M6·M7·M8·M9의 추가 테이블 마이그레이션을 차례로 적용한다. 일반화된 마이그레이션 버전 관리·롤백 체계는 아직 없다.
- `noah.users`는 인증된 사용자 Principal이며, DDR-005의 보호된 NOAH Identity Core 구현이 아니다.
- 목록 커서는 페이지 위치를 표현하며 여러 요청에 걸친 고정 DB 스냅샷은 제공하지 않는다. 페이지 이동 중 메모 또는 프로젝트 소속이 바뀌면 이후 결과에 반영된다.
- M1 개별 조회 `GET /memories/<id>`, M2 목록 조회 `GET /memories`, M3 자연어 조회 `POST /memories/query`는 Task·실행 기록을 새로 생성하지 않는다. M6·M7 읽기 전용 Tool은 실행 시작 전 Task·Execution을 생성하고 검증된 Evidence를 연결한다.
- 로컬 서버를 `Ctrl+C`로 종료하면 현재 `KeyboardInterrupt` traceback이 표시된다. 종료 UX 개선 후보이며 메모 조회 기능의 차단 문제는 아니다.
- M3 단어 검색은 모든 단어가 포함된 메모만 찾는다. 동의어·형태소·의미 검색은 없고, 답변 검토는 최대 5건이다. 일치 문구의 출처는 검증하지만 메모 내용의 현실 세계 사실성은 검증하지 않는다.
- NOAH 전용 Ollama는 별도 PowerShell 창에서 `127.0.0.1:11435`로 실행해야 하며 CPU 전용 응답은 수십 초 걸릴 수 있다. 기존 전역 Ollama는 `0.0.0.0:11434`에 리스닝 중이다. 현재 방화벽 규칙은 접근 거부로 확인하지 못했다. 기존 원격 의존성에 영향을 주지 않기 위해 그 설정은 변경하지 않았다.
- M3 자연어 읽기는 기존 GET처럼 Task·실행 기록을 새로 생성하지 않는다. 모델 답변은 원문 발췌로 제한하며 자유로운 서술식 합성은 제공하지 않는다.
- `gemma4:12b-it-qat`는 M3에서 합성 요청과 실사용으로 검증한 **현재 기준 모델**이며 NOAH의 영구 최종 모델로 확정한 것은 아니다. GPU 사용 방식과 모델별 성능·품질 비교는 별도 후속 검토 항목이다.

## 미구현 기능과 다음 후보

이번 Slice에는 멀티에이전트, 자율적 Task 생성, 자기 수정, 장기 기억 자동 추출, 벡터 검색, n8n 연동, 대규모 프론트엔드 및 새 Agent Framework가 포함되지 않는다. LLM은 읽기 의도 제안과 근거 발췌에만 사용한다. Artifact·Knowledge·Identity Core의 전체 영속화도 구현하지 않았다.

M9의 자동·사용자 수동 검증이 완료됐으며 다음 단계는 최종 검토 후 승인에 따른 커밋·Push다. 자유 형식 요약, Memory 결합, 자동 검색 및 3개 이상 문서는 여전히 범위 밖이다. 이후 후보는 제한된 출처별 요약 계약 또는 읽기 전용 Tool의 Recovery 진단 확대이다. M5 후속 안전 복구 계약, M6–M9 Tool의 same-user 로컬 경로 교체 공격 대응, 정상 서버 종료 처리, 사용자 주도 메모 삭제도 별도 후보이다. 모델의 CPU/GPU 운용 및 성능 비교와 기존 `11434` Ollama 서비스의 네트워크 노출도 후속 검토 항목이다. 다른 프로젝트의 원격 사용 여부 확인 없이 전역 설정을 변경하지 않는다.

## 아키텍처 기준선

관련 Blueprint: [Task](../02-Architecture/Core/Task.md), [Agent](../02-Architecture/Core/Agent.md), [Identity](../02-Architecture/Core/Identity.md), [State](../02-Architecture/Runtime/State.md), [Session](../02-Architecture/Runtime/Session.md), [Runtime](../02-Architecture/Runtime/Runtime.md), [Harness](../02-Architecture/Runtime/Harness.md), [Context](../02-Architecture/Runtime/Context.md), [Memory](../02-Architecture/Information/Memory.md), [Knowledge](../02-Architecture/Information/Knowledge.md).

Accepted DDR: [DDR-001 Task State / Runtime](../02-Architecture/Decisions/DDR-001-task-state-runtime-boundary.md), [DDR-002 Harness](../02-Architecture/Decisions/DDR-002-harness-boundary.md), [DDR-003 Memory / Knowledge](../02-Architecture/Decisions/DDR-003-memory-knowledge-boundary.md), [DDR-004 Artifact](../02-Architecture/Decisions/DDR-004-artifact-architecture.md), [DDR-005 Identity](../02-Architecture/Decisions/DDR-005-identity-persistence.md), [DDR-006 Orchestration](../02-Architecture/Decisions/DDR-006-orchestration-contract.md).

구현 현황은 위 설계의 일부 경계를 검증한 결과이며, Blueprint·DDR의 모든 수용 기준을 완료했다는 뜻은 아니다. 설계 변경이 필요한 경우 관련 DDR과의 관계 및 변경 이유를 먼저 보고한다.

## 기능별 개발 절차

1. 현재 Blueprint와 Accepted DDR을 확인한다.
2. 기능의 구현 범위와 제외 범위를 정의한다.
3. 필요한 코드를 구현한다.
4. 테스트와 실제 실행을 검증한다.
5. 검증 결과를 기록한다.
6. 이 개발 현황 문서를 갱신한다.
7. 변경 사항과 비밀정보 포함 여부를 검토한다.
8. 사용자 승인 후 Git 커밋과 Push를 진행한다.
