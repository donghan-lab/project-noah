# NOAH 개발 현황

> 기준일: 2026-09-28 (Asia/Seoul)
> 성격: 구현·검증 진행 상황의 요약. 기존 Blueprint와 Accepted DDR을 대체하거나 변경하지 않는다.
> 첫 Slice 기준 커밋: `061dbea` — 인증된 PostgreSQL 메모 저장 구현. 이후 반영 상태는 Git 기록을 따른다.

## 현재 마일스톤

**M6 — 첫 Read-only Tool Execution:** 프로젝트 권한을 확인한 뒤 운영자 로컬 allowlist의 고정 문서 루트에서 직접 하위 `.md` 파일명만 조회한다. 합성 프로젝트와 Docker Compose PostgreSQL 17·로컬 Ollama에서 검증했으며, M1–M5 회귀 테스트를 유지했다. 실제 사용자 프로젝트는 아직 등록하지 않았다. 저장소 반영 상태는 Git 기록을 따른다.

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
- 기존 `compose/.env`와 Docker Compose PostgreSQL 설정을 사용한다. 로컬 운영 명령으로 스키마 초기화, 사용자 토큰 발급 및 프로젝트 생성을 지원한다.

구현 위치: [`noah/`](../../noah/), [`database/001_first_slice.sql`](../../database/001_first_slice.sql), [`database/002_memory_write_idempotency.sql`](../../database/002_memory_write_idempotency.sql), [`database/003_document_tool_evidence.sql`](../../database/003_document_tool_evidence.sql), [`tests/`](../../tests/). 실행 절차: [First vertical slice](13-First-Vertical-Slice.md), [Second vertical slice](15-Second-Vertical-Slice.md), [Third vertical slice](17-Third-Vertical-Slice.md), [Fourth vertical slice](19-Fourth-Vertical-Slice.md), [M5 read-only triage](21-Fifth-Vertical-Slice.md), [M6 Tool Execution](23-Sixth-Vertical-Slice.md). M2·M3·M5에는 DB 스키마 변경이 없었고, M4·M6는 각각 기존 데이터를 유지하는 추가 테이블을 마이그레이션했다.

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

M1 Compose 테스트는 실제 외래 키 위반에 따른 메모 쓰기 롤백과 실패 Task·실행 기록을 확인했다. M1의 재시작 검증은 HTTP 서버 인스턴스를 **같은 Python 프로세스에서** 종료·재생성한 것이고, M4는 별도 테스트에서 NOAH Python 서버 **프로세스 자체를** 종료·재시작한 뒤 동일 키 재요청을 확인했다. 자동 테스트용 행은 정리했고, `noah` 스키마의 기존 7개 테이블과 M4 추가 매핑 테이블을 유지했다. 기존 Compose 컨테이너와 named volume은 테스트 전후 동일한 것으로 확인했다.

M1 상세 근거와 실패 주입 기록: [First Slice Validation Record](14-First-Slice-Validation.md). M2 검증 및 기존 사용자 데이터 보존 결과: [Second Slice Validation Record](16-Second-Slice-Validation.md). M3 모델 비교, 안전한 로컬 리스너, 실제 Compose·Ollama 검증: [Third Slice Validation Record](18-Third-Slice-Validation.md). M4의 마이그레이션, 동시 요청, 실제 서버 프로세스 재시작과 M1–M3 회귀 검증: [Fourth Slice Validation Record](20-Fourth-Slice-Validation.md).

2026-09-28 사용자 수동 검증에서는 NOAH 전용 Ollama의 루프백 리스너와 모델 등록, 인증 거부 동작을 확인했다. 기존 개인 메모에 대한 자연어 질문은 `succeeded/grounded`, `scope=all`, `examined=1`, `truncated=false`로 응답했고, 사용자는 근거 ID와 원문 발췌를 확인했다. 개인 메모 원문과 인증정보는 [M3 검증 기록](18-Third-Slice-Validation.md)에 넣지 않았다.

M4의 **별도 사용자 수동 검증**에서 공개용 테스트 메모의 첫 저장은 HTTP 201, 동일 키·동일 본문 재요청은 HTTP 200과 `replayed: true`였으며 memory_id·task_id·execution_id가 모두 같았다. 동일 키에 다른 내용을 보낸 요청은 HTTP 409와 `IDEMPOTENCY_CONFLICT`였다. 읽기 전용 DB 확인 결과, 수동 테스트 전→후 사용자 **1→1**, 활성 토큰 **1→1**, 개인 메모 **1→2**, Task **1→2**, Execution Record **1→3**, 키 매핑 **0→1**이었다. 재요청은 새 메모·Task·Execution Record를 만들지 않았고, 충돌은 메모나 Task 없이 실패 Execution Record 한 건만 남겼다. 기존 사용자·토큰·이전 개인 메모는 유지되며 `running` Task와 Execution Record는 각각 0건이다. 자세한 참조 관계는 [M4 검증 기록](20-Fourth-Slice-Validation.md)에 보존했다.

M5에서는 합성 자료로 완료·확정 실패·예약 후 미종결·응답 유실·상태/참조 불일치·DB 연결 실패를 점검했다. 진단 전후 합성 Task·Execution·Memory·매핑 행이 동일했으며 테스트 소유 행만 정리했다. 기존 DB의 별도 읽기 전용 진단 결과는 검증 완료 2건, 기록된 실패 1건, 미종결 및 불일치 0건이었다. 정확한 시험 범위와 실제 Ollama 호출 건너뜀은 [M5 검증 기록](22-Fifth-Slice-Validation.md)에 남겼다.

M5의 **별도 사용자 수동 검증**에서도 `recovery-report`가 `succeeded`, 검사 3건, 검증 완료 2건, 기록된 실패 1건을 반환했다. 미종결 running 및 기록 불일치는 보고되지 않았고 세 항목 모두 `issues: []`였다. 완료된 두 항목은 `completed/succeeded/passed`와 검증 시각·메모 참조·실제 메모 존재를 표시했다. 한 항목에만 키 매핑이 있는 것은 기존 무키 저장과 M4 이후 키 저장 이력에 부합하지만, 매핑 유무만으로 생성 시기를 증명하지는 않는다. 수동 관찰의 자세한 내용은 [M5 검증 기록](22-Fifth-Slice-Validation.md)에 자동 테스트와 구분하여 남겼다.

M6 합성 검증에서는 실제 사용자 데이터와 분리된 프로젝트·membership·임시 문서 루트로 HTTP 경로, 제한된 실제 Ollama 의도, 파일명 검증, Task/Execution/Evidence 연결을 확인했다. 테스트 소유 행 정리 뒤 사용자 1명·토큰 1건·개인 메모 2건·Task 2건·Execution 3건·M4 키 매핑 1건은 유지됐고 프로젝트·membership·M6 evidence는 0건이었다. 자세한 제한과 테스트 결과는 [M6 검증 기록](24-Sixth-Slice-Validation.md)에 있다.

M6의 **별도 사용자 수동 검증**에서는 Windows PowerShell 5.1의 `application/json` 요청에서 한국어가 손상되어 `UNSUPPORTED_INTENT`가 반환됐다. `charset=utf-8`을 지정하자 같은 한국어 질문의 intent가 통과했다. BOM이 든 local mapping에서는 `PROJECT_ROOT_CONFIG_INVALID`였고, BOM 없는 mapping으로 다시 저장한 뒤 `project.documents.list`가 성공했다. 응답에는 합성 `alpha.md`, `beta.md`, `gamma.md`만 있었고 비 `.md` 파일, 본문, 절대경로는 없었다. 사용자는 Task·Execution·Tool Evidence 및 hash를 확인하고 임시 행·mapping·문서 루트를 정리했다. 별도 읽기 전용 확인에서 기존 사용자 1·토큰 1·메모 2·Task 2·Execution 3·M4 매핑 1, 프로젝트·membership·M6 evidence·running 기록 0건이었다. 실행 안내의 UTF-8 전송·BOM 없는 저장 예시와 BOM 유무를 허용하는 로더를 보완했다. 수동 결과와 자동 테스트는 [M6 검증 기록](24-Sixth-Slice-Validation.md)에 구분해 남겼다.

## 알려진 제한 사항

- 메모 쓰기 멱등성은 새 요청의 선택적 키에만 적용된다. 키 없는 과거·현재 쓰기는 재시도로 중복될 수 있고, 확정 실패를 같은 키로 자동 재실행하지 않는다. 커밋 결과가 불확실할 때는 같은 키로 내구 상태를 재조회할 수 있으나 자동 복구는 없다.
- DB 연결이 실행 중 끊어지면 로컬 실패 기록은 남길 수 있지만, DB에 남은 `running` Task를 자동으로 복구·정리하는 기능은 없다.
- M5 진단은 현재 `memory.save`에 한정된다. `running`에서 Runtime 생존 여부나 최종 커밋 가능성을 판단할 지속적 소유권·fencing 근거가 없으므로 자동 상태 전이와 쓰기 재실행을 하지 않는다. Task의 현행 goal 문자열로 범위를 식별하므로 향후 일반화에는 명시적 capability 연계가 필요하다.
- M6의 프로젝트→문서 루트 mapping은 운영자 로컬 설정에서만 제공한다. 현재 실제 프로젝트와 membership이 각각 0건이므로 운영자가 범위를 등록하기 전에는 실제 사용자 대상 Tool 조회를 할 수 없다. M6 결과는 조회 시점의 파일명 관찰이며 파일 내용·후속 변경을 보증하지 않는다.
- M6 경로 보장은 사용자·모델·원격 입력을 통한 탈출에 초점을 둔다. 동일 Windows 사용자 권한의 악성 로컬 프로세스가 검사와 열거 사이에 링크를 바꾸는 공격까지 보장하지 않는다. Windows 테스트 계정에서 실제 symlink 생성은 허용되지 않아 해당 제외 분기는 합성 reparse 속성으로 시험했다.
- HTTP API는 로컬호스트에만 바인딩한다. 원격 배포용 TLS, 운영 인증·권한 관리, 속도 제한은 범위 밖이다.
- `noah init`은 첫 스키마와 M4·M6의 추가 테이블 마이그레이션을 차례로 적용한다. 일반화된 마이그레이션 버전 관리·롤백 체계는 아직 없다.
- `noah.users`는 인증된 사용자 Principal이며, DDR-005의 보호된 NOAH Identity Core 구현이 아니다.
- 목록 커서는 페이지 위치를 표현하며 여러 요청에 걸친 고정 DB 스냅샷은 제공하지 않는다. 페이지 이동 중 메모 또는 프로젝트 소속이 바뀌면 이후 결과에 반영된다.
- 읽기 요청은 기존 개별 메모 조회와 같이 Task·실행 기록을 새로 생성하지 않는다.
- 로컬 서버를 `Ctrl+C`로 종료하면 현재 `KeyboardInterrupt` traceback이 표시된다. 종료 UX 개선 후보이며 메모 조회 기능의 차단 문제는 아니다.
- M3 단어 검색은 모든 단어가 포함된 메모만 찾는다. 동의어·형태소·의미 검색은 없고, 답변 검토는 최대 5건이다. 일치 문구의 출처는 검증하지만 메모 내용의 현실 세계 사실성은 검증하지 않는다.
- NOAH 전용 Ollama는 별도 PowerShell 창에서 `127.0.0.1:11435`로 실행해야 하며 CPU 전용 응답은 수십 초 걸릴 수 있다. 기존 전역 Ollama는 `0.0.0.0:11434`에 리스닝 중이다. 현재 방화벽 규칙은 접근 거부로 확인하지 못했다. 기존 원격 의존성에 영향을 주지 않기 위해 그 설정은 변경하지 않았다.
- M3 자연어 읽기는 기존 GET처럼 Task·실행 기록을 새로 생성하지 않는다. 모델 답변은 원문 발췌로 제한하며 자유로운 서술식 합성은 제공하지 않는다.
- `gemma4:12b-it-qat`는 M3에서 합성 요청과 실사용으로 검증한 **현재 기준 모델**이며 NOAH의 영구 최종 모델로 확정한 것은 아니다. GPU 사용 방식과 모델별 성능·품질 비교는 별도 후속 검토 항목이다.

## 미구현 기능과 다음 후보

이번 Slice에는 멀티에이전트, 자율적 Task 생성, 자기 수정, 장기 기억 자동 추출, 벡터 검색, n8n 연동, 대규모 프론트엔드 및 새 Agent Framework가 포함되지 않는다. LLM은 읽기 의도 제안과 근거 발췌에만 사용한다. Artifact·Knowledge·Identity Core의 전체 영속화도 구현하지 않았다.

다음 M7 **후보**는 승인된 프로젝트 문서의 제한적 본문 읽기 또는 M5 후속 안전 복구 계약이다. 본문 읽기로 확장하려면 권한·크기·민감정보·근거 검증을 별도로 설계해야 한다. M6 Tool의 same-user 로컬 경로 교체 공격 대응, 정상 서버 종료 처리, 사용자 주도 메모 삭제도 별도 후보이다. 모델의 CPU/GPU 운용 및 성능 비교와 기존 `11434` Ollama 서비스의 네트워크 노출도 후속 검토 항목이다. 다른 프로젝트의 원격 사용 여부 확인 없이 전역 설정을 변경하지 않는다.

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
