# NOAH 개발 현황

> 기준일: 2026-09-28 (Asia/Seoul)
> 성격: 구현·검증 진행 상황의 요약. 기존 Blueprint와 Accepted DDR을 대체하거나 변경하지 않는다.
> 첫 Slice 기준 커밋: `061dbea` — 인증된 PostgreSQL 메모 저장 구현. 이후 반영 상태는 Git 기록을 따른다.

## 현재 마일스톤

**M4 — Memory Write Idempotency Vertical Slice:** 구현과 기존 Docker Compose PostgreSQL 17에서의 자동·사용자 수동 검증 완료. 선택적 작업 재시도 키로 같은 논리적 저장의 중복 실행을 막고, 성공·진행 중·충돌·확정 실패·커밋 결과 불확실 상태를 구분한다. M1 메모 저장, M2 권한 적용 조회, M3 읽기 전용 Local LLM Query도 회귀 테스트로 유지됨을 확인했다. 저장소 반영 상태는 Git 기록을 따른다.

## 완료된 기능과 구현 범위

- 로컬 HTTP `POST /memories`: 명시적 `save_memory` 요청만 처리한다.
- PostgreSQL에 저장한 해시로 bearer token을 인증하고, 개인 메모의 소유자 또는 프로젝트 쓰기 권한을 확인한다.
- 입력 및 저장 범위를 검증하고, 메모를 PostgreSQL에 저장한 뒤 DB에서 재조회해 결과를 확인한다.
- 선택적 `Idempotency-Key`를 사용자별로 PostgreSQL에 예약한다. 같은 요청의 성공 재시도는 기존 메모·Task·실행 ID를 돌려주고, 다른 요청 내용이면 충돌을 반환한다. 동시 요청과 서버 프로세스 재시작 후에도 중복 저장을 막는다. 키 없는 기존 API 동작은 유지한다.
- Task의 지속 상태와 실행 기록을 별도 테이블에 남긴다. 성공에는 메모 ID와 재조회 증거를, 거부·실패에는 구조화된 실패 코드를 반환한다.
- `GET /memories/<id>`는 같은 범위 권한으로 저장된 메모를 조회한다.
- `GET /memories`는 인증된 사용자가 읽을 수 있는 개인·프로젝트 메모만 반환한다. 프로젝트 소속 사용자는 쓰기 권한이 없어도 읽을 수 있다. 생성 시각과 ID의 역순 정렬 및 커서 페이지네이션을 제공한다.
- `POST /memories/query`는 토큰 인증 후 로컬 Ollama가 제안한 읽기 의도와 질문의 단어를 검증한다. 기존 개인·프로젝트 조회 권한 필터를 공유하는 매개변수화 검색으로 최대 5건을 조회하고, 제한된 본문을 모델에 전달한다. 답변에는 실제 조회 결과의 ID와 원문이 일치하는 발췌만 사용한다. 빈 결과·근거 부족·검색 한도와 DB/모델 오류를 구분한다.
- 기존 `compose/.env`와 Docker Compose PostgreSQL 설정을 사용한다. 로컬 운영 명령으로 스키마 초기화, 사용자 토큰 발급 및 프로젝트 생성을 지원한다.

구현 위치: [`noah/`](../../noah/), [`database/001_first_slice.sql`](../../database/001_first_slice.sql), [`database/002_memory_write_idempotency.sql`](../../database/002_memory_write_idempotency.sql), [`tests/test_first_slice.py`](../../tests/test_first_slice.py), [`tests/test_memory_read.py`](../../tests/test_memory_read.py), [`tests/test_memory_query.py`](../../tests/test_memory_query.py), [`tests/test_memory_idempotency.py`](../../tests/test_memory_idempotency.py). 실행 절차: [First vertical slice](13-First-Vertical-Slice.md), [Second vertical slice](15-Second-Vertical-Slice.md), [Third vertical slice](17-Third-Vertical-Slice.md), [Fourth vertical slice](19-Fourth-Vertical-Slice.md). M2와 M3에는 DB 스키마 변경이 없었고, M4는 추가 테이블 하나를 마이그레이션한다.

## 테스트 및 검증

| 환경 | 마지막 실행 | 결과 | 범위 |
| --- | --- | --- | --- |
| 격리 PostgreSQL 18 | 2026-09-24 | 5개 통과, 실패·오류·건너뜀 0개 | DB 통합 테스트 4개와 의도적인 DB 연결 실패 테스트 1개 |
| 기존 Docker Compose PostgreSQL 17 | 2026-09-25 | 5개 통과, 실패·오류·건너뜀 0개 | DB 통합 테스트 4개와 의도적인 DB 연결 실패 테스트 1개 |
| 기존 Docker Compose PostgreSQL 17 — M2 | 2026-09-27 | 메모 목록 테스트 7개와 M1 회귀 테스트 4개 통과, 실패·오류·건너뜀 0개 | 실제 DB의 권한 필터, 빈 목록, 정렬·페이지네이션, HTTP 조회, 메모 저장·롤백 회귀 |
| 기존 Docker Compose PostgreSQL 17 + 로컬 Ollama — M3 | 2026-09-28 | 전체 24개 재실행 통과, 실패·오류·건너뜀 0개 | 합성 사용자·메모의 인증, 개인·프로젝트 권한, 근거 검증, 모델·DB 오류, Write/Read 회귀 |
| 기존 Docker Compose PostgreSQL 17 + 로컬 Ollama — M4 | 2026-09-28 | 전용 테스트 6개 및 전체 30개 통과, 실패·오류·건너뜀 0개 | 키 재시도·충돌·동시성·롤백·커밋 응답 유실·실제 서버 프로세스 재시작, M1–M3 회귀와 합성 메모의 실제 Ollama 호출 |

M1 Compose 테스트는 실제 외래 키 위반에 따른 메모 쓰기 롤백과 실패 Task·실행 기록을 확인했다. M1의 재시작 검증은 HTTP 서버 인스턴스를 **같은 Python 프로세스에서** 종료·재생성한 것이고, M4는 별도 테스트에서 NOAH Python 서버 **프로세스 자체를** 종료·재시작한 뒤 동일 키 재요청을 확인했다. 자동 테스트용 행은 정리했고, `noah` 스키마의 기존 7개 테이블과 M4 추가 매핑 테이블을 유지했다. 기존 Compose 컨테이너와 named volume은 테스트 전후 동일한 것으로 확인했다.

M1 상세 근거와 실패 주입 기록: [First Slice Validation Record](14-First-Slice-Validation.md). M2 검증 및 기존 사용자 데이터 보존 결과: [Second Slice Validation Record](16-Second-Slice-Validation.md). M3 모델 비교, 안전한 로컬 리스너, 실제 Compose·Ollama 검증: [Third Slice Validation Record](18-Third-Slice-Validation.md). M4의 마이그레이션, 동시 요청, 실제 서버 프로세스 재시작과 M1–M3 회귀 검증: [Fourth Slice Validation Record](20-Fourth-Slice-Validation.md).

2026-09-28 사용자 수동 검증에서는 NOAH 전용 Ollama의 루프백 리스너와 모델 등록, 인증 거부 동작을 확인했다. 기존 개인 메모에 대한 자연어 질문은 `succeeded/grounded`, `scope=all`, `examined=1`, `truncated=false`로 응답했고, 사용자는 근거 ID와 원문 발췌를 확인했다. 개인 메모 원문과 인증정보는 [M3 검증 기록](18-Third-Slice-Validation.md)에 넣지 않았다.

M4의 **별도 사용자 수동 검증**에서 공개용 테스트 메모의 첫 저장은 HTTP 201, 동일 키·동일 본문 재요청은 HTTP 200과 `replayed: true`였으며 memory_id·task_id·execution_id가 모두 같았다. 동일 키에 다른 내용을 보낸 요청은 HTTP 409와 `IDEMPOTENCY_CONFLICT`였다. 읽기 전용 DB 확인 결과, 수동 테스트 전→후 사용자 **1→1**, 활성 토큰 **1→1**, 개인 메모 **1→2**, Task **1→2**, Execution Record **1→3**, 키 매핑 **0→1**이었다. 재요청은 새 메모·Task·Execution Record를 만들지 않았고, 충돌은 메모나 Task 없이 실패 Execution Record 한 건만 남겼다. 기존 사용자·토큰·이전 개인 메모는 유지되며 `running` Task와 Execution Record는 각각 0건이다. 자세한 참조 관계는 [M4 검증 기록](20-Fourth-Slice-Validation.md)에 보존했다.

## 알려진 제한 사항

- 메모 쓰기 멱등성은 새 요청의 선택적 키에만 적용된다. 키 없는 과거·현재 쓰기는 재시도로 중복될 수 있고, 확정 실패를 같은 키로 자동 재실행하지 않는다. 커밋 결과가 불확실할 때는 같은 키로 내구 상태를 재조회할 수 있으나 자동 복구는 없다.
- DB 연결이 실행 중 끊어지면 로컬 실패 기록은 남길 수 있지만, DB에 남은 `running` Task를 자동으로 복구·정리하는 기능은 없다.
- HTTP API는 로컬호스트에만 바인딩한다. 원격 배포용 TLS, 운영 인증·권한 관리, 속도 제한은 범위 밖이다.
- `noah init`은 첫 스키마와 M4의 추가 테이블 마이그레이션을 차례로 적용한다. 일반화된 마이그레이션 버전 관리·롤백 체계는 아직 없다.
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

다음 Vertical Slice **후보**는 Memory Reliability의 다음 단계인 장애 후 `running` Task의 안전한 판별·복구 또는 정상 서버 종료 처리, 이후 사용자 주도 메모 삭제다. 모델의 CPU/GPU 운용 및 성능 비교와 기존 `11434` Ollama 서비스의 네트워크 노출도 별도 후속 검토 항목이다. 다른 프로젝트의 원격 사용 여부 확인 없이 전역 설정을 변경하지 않는다.

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
