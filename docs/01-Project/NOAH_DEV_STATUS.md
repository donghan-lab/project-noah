# NOAH 개발 현황

> 기준일: 2026-09-27 (Asia/Seoul)
> 성격: 구현·검증 진행 상황의 요약. 기존 Blueprint와 Accepted DDR을 대체하거나 변경하지 않는다.
> 마지막 구현 커밋: `061dbea` — `feat: add authenticated PostgreSQL memory save vertical slice`

## 현재 마일스톤

**M1 — 명시적 메모 저장 Vertical Slice:** 구현과 PostgreSQL 통합 검증 완료. 현재 단계는 검증 기록 정정 및 개발 현황 문서의 사용자 검토다. 다음 마일스톤의 범위는 아직 확정하지 않았다.

## 완료된 기능과 구현 범위

- 로컬 HTTP `POST /memories`: 명시적 `save_memory` 요청만 처리한다.
- PostgreSQL에 저장한 해시로 bearer token을 인증하고, 개인 메모의 소유자 또는 프로젝트 쓰기 권한을 확인한다.
- 입력 및 저장 범위를 검증하고, 메모를 PostgreSQL에 저장한 뒤 DB에서 재조회해 결과를 확인한다.
- Task의 지속 상태와 실행 기록을 별도 테이블에 남긴다. 성공에는 메모 ID와 재조회 증거를, 거부·실패에는 구조화된 실패 코드를 반환한다.
- `GET /memories/<id>`는 같은 범위 권한으로 저장된 메모를 조회한다.
- 기존 `compose/.env`와 Docker Compose PostgreSQL 설정을 사용한다. 로컬 운영 명령으로 스키마 초기화, 사용자 토큰 발급 및 프로젝트 생성을 지원한다.

구현 위치: [`noah/`](../../noah/), [`database/001_first_slice.sql`](../../database/001_first_slice.sql), [`tests/test_first_slice.py`](../../tests/test_first_slice.py). 실행 절차: [First vertical slice](13-First-Vertical-Slice.md).

## 테스트 및 검증

| 환경 | 마지막 실행 | 결과 | 범위 |
| --- | --- | --- | --- |
| 격리 PostgreSQL 18 | 2026-09-24 | 5개 통과, 실패·오류·건너뜀 0개 | DB 통합 테스트 4개와 의도적인 DB 연결 실패 테스트 1개 |
| 기존 Docker Compose PostgreSQL 17 | 2026-09-25 | 5개 통과, 실패·오류·건너뜀 0개 | DB 통합 테스트 4개와 의도적인 DB 연결 실패 테스트 1개 |

Compose 테스트는 실제 외래 키 위반에 따른 메모 쓰기 롤백과 실패 Task·실행 기록을 확인했다. HTTP 서버 인스턴스를 **같은 Python 프로세스에서** 종료·재생성한 뒤 메모 재조회를 확인했다. Python 프로세스 자체의 재시작 테스트는 아직 없다. 테스트용 행은 정리했고, `noah` 스키마와 7개 테이블은 유지했다. 기존 Compose 컨테이너와 named volume은 테스트 전후 동일한 것으로 확인했다.

상세 근거와 실패 주입 기록: [First Slice Validation Record](14-First-Slice-Validation.md). 이 문서 갱신을 위해 테스트를 다시 실행하지 않았다.

## 알려진 제한 사항

- 메모 쓰기는 현재 비멱등 작업이다. 재시도 중복 방지 키와 불확실한 커밋 결과의 자동 조정은 없다.
- DB 연결이 실행 중 끊어지면 로컬 실패 기록은 남길 수 있지만, DB에 남은 `running` Task를 자동으로 복구·정리하는 기능은 없다.
- HTTP API는 로컬호스트에만 바인딩한다. 원격 배포용 TLS, 운영 인증·권한 관리, 속도 제한은 범위 밖이다.
- 초기 SQL은 첫 스키마 생성용이다. 이후 버전의 스키마 마이그레이션 절차는 마련되지 않았다.
- `noah.users`는 인증된 사용자 Principal이며, DDR-005의 보호된 NOAH Identity Core 구현이 아니다.

## 미구현 기능과 다음 후보

이번 Slice에는 멀티에이전트, 자율적 Task 생성, 자기 수정, 장기 기억 자동 추출, 벡터 검색, n8n 연동, 대규모 프론트엔드, LLM 및 새 Agent Framework가 포함되지 않는다. Artifact·Knowledge·Identity Core의 전체 영속화도 이 Slice에서 구현하지 않았다.

다음 Vertical Slice **후보**는 권한이 적용된 메모 목록 조회와 사용자 주도 삭제다. 범위를 확정하기 전에 비멱등 쓰기의 재시도 처리와 실패 후 Task 정리의 우선순위도 검토한다.

## 아키텍처 기준선

관련 Blueprint: [Task](../02-Architecture/Core/Task.md), [Agent](../02-Architecture/Core/Agent.md), [Identity](../02-Architecture/Core/Identity.md), [Session](../02-Architecture/Runtime/Session.md), [Runtime](../02-Architecture/Runtime/Runtime.md), [Harness](../02-Architecture/Runtime/Harness.md), [Context](../02-Architecture/Runtime/Context.md), [Memory](../02-Architecture/Information/Memory.md), [Knowledge](../02-Architecture/Information/Knowledge.md).

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
