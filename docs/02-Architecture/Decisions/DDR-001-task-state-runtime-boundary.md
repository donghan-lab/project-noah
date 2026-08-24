# DDR-001 — Task State / Runtime Boundary

> Project NOAH Architecture Decision Record
> Decision ID: DDR-001
> Status: Accepted
> Date: 2026-08-24

---

# 1. Decision

Project NOAH는 Task State와 Runtime을 서로 다른 책임을 가진 Architecture Boundary로 분리한다.

Task는 장기적인 목표와 진행 상태를 표현하며,
Runtime은 실제 Execution Lifecycle을 관리한다.

핵심 원칙:

```text
Task
≠
Runtime

그리고:

Task State
≠
Execution State

로 정의한다.

2. Context

Architecture Integration Review와 다음 Research를 통해
Session, Task, Context, State, Runtime의 책임이 서로 겹칠 가능성이 확인되었다.

특히 다음 요구사항을 충족하기 위해 명확한 경계가 필요하다.

Long-running Task
Pause / Resume
Runtime replacement
Failure recovery
Checkpoint
Context reconstruction
Multi-session continuity
Evaluation
Artifact persistence

Runtime이 종료되더라도 Task 자체가 사라져서는 안 된다.

3. Problem

다음 구조는 장기적으로 문제가 발생할 수 있다.

Session
 ↓
Runtime
 ↓
Everything

이 구조에서는:

Runtime 종료 시 Task 상태 유실
Session과 Task lifecycle 결합
Recovery 어려움
Runtime 교체 어려움
Context와 State 혼합
Long-horizon Task 지원 어려움

이 발생할 가능성이 있다.

4. Decision Scope

이번 Decision에서 정의하는 대상:

Task
Session
Task State
Execution State
Runtime
Context
Checkpoint
Recovery

이번 Decision에서는 다음을 최종 결정하지 않는다.

구체적인 Database
Runtime Framework
Event Sourcing
최종 Checkpoint Storage
Distributed Execution
5. Task Definition

Task는 사용자가 달성하고자 하는 지속적인 목표를 표현한다.

후보 구조:

Task
├── ID
├── Goal
├── Requirements
├── Constraints
├── Status
├── Progress
├── Plan Reference
├── Artifact References
└── Verification Status

Task는 Session보다 오래 지속될 수 있다.

6. Session Definition

Session은 특정 실행 관계를 표현한다.

예:

Task
├── Session A
├── Session B
└── Session C

따라서:

Task Lifetime
≥
Session Lifetime

이라는 원칙을 사용한다.

7. Task State

Task State는 Task의 현재 canonical progress를 표현한다.

후보:

Task State
├── Status
├── Progress
├── Current Plan
├── Completed Work
├── Pending Work
├── Blockers
├── Artifact References
└── Verification Status

Task State는 Runtime과 독립적으로 유지되어야 한다.

8. Execution State

Execution State는 현재 Runtime 실행에 필요한 상태다.

후보:

Execution State
├── Current Turn
├── Active Tool
├── Retry Count
├── Approval State
├── Runtime Instance
├── Checkpoint
└── Error State

Execution State는 Runtime 교체에 따라 달라질 수 있다.

9. Runtime

Runtime은 실제 Agent Execution Lifecycle을 관리한다.

책임:

Start
Run
Pause
Resume
Cancel
Retry
Checkpoint
Recover
Observe

Runtime은 Task의 목표나 장기적인 의미를 소유하지 않는다.

10. Context

Context는 Model-facing projection이다.

Task State
+
Memory
+
Knowledge
+
Artifacts
+
Conversation
+
Environment Observation
+
Policy
        ↓
Context
        ↓
Model

Context는 canonical state가 아니다.

11. Canonical State

Task의 canonical state는 Runtime Memory가 아니라
durable Task State가 담당한다.

원칙:

Runtime
→ executes

Task State
→ persists canonical progress
12. Pause / Resume

Task는 Runtime 종료 이후에도 재개할 수 있어야 한다.

예:

Runtime A
 ↓
Checkpoint
 ↓
Pause
 ↓
Runtime A 종료
 ↓
Runtime B
 ↓
Restore Task State
 ↓
Reconstruct Context
 ↓
Resume
13. Context Reconstruction

Resume 시 이전 Model Context를 무조건 그대로 복원하지 않는다.

대신:

Task State
+
Memory
+
Knowledge
+
Relevant History
+
Workspace / Environment Observation
+
Policy
        ↓
New Context

를 통해 현재 실행에 맞는 Context를 재구성할 수 있어야 한다.

14. Runtime Replacement

Runtime은 교체 가능한 구현이어야 한다.

예:

Runtime A
 ↓
Runtime B

로 변경되어도:

Task
Task State
Artifacts
Memory
Identity

의 지속성이 깨지지 않아야 한다.

15. Failure Recovery

Runtime 실패 시:

Runtime Failure
 ↓
Persisted Task State
 ↓
Recovery
 ↓
New Runtime
 ↓
Resume

가 가능해야 한다.

16. Tool Side Effects

Runtime Recovery에서 가장 큰 위험 중 하나는
외부 Side Effect가 이미 발생한 상태에서 재실행하는 것이다.

예:

send_email()
 ↓
External Side Effect
 ↓
Runtime Crash
 ↓
Retry

이 경우 중복 실행 가능성이 있다.

따라서:

Idempotency
Execution Record
Side Effect Tracking
Compensation

을 후속 설계에서 고려한다.

17. Checkpoint

Checkpoint는 작업을 나중에 재개할 수 있을 만큼의 durable execution information을 보존한다.

후보:

Task State
+
Execution Metadata
+
Artifact References
+
Relevant Workspace State

전체 Context를 반드시 Snapshot하지는 않는다.

18. Event Log

Execution Event는 observability와 recovery에 사용될 수 있다.

예:

TaskCreated
TaskUpdated
ExecutionStarted
ToolCalled
ToolCompleted
CheckpointCreated
ExecutionPaused
ExecutionResumed
VerificationPassed
TaskCompleted

Event Log를 Canonical Source of Truth로 사용할지는 별도 Decision으로 남긴다.

19. Event Sourcing

Full Event Sourcing은 현재 확정하지 않는다.

상태:

Deferred

이유:

초기 복잡도
Schema evolution
Storage overhead
실제 필요성 미검증

향후 PoC에서 필요성이 확인되면 별도 DDR을 작성한다.

20. Long-Horizon Tasks

Task는 Session보다 장기간 지속될 수 있다.

예:

Task
├── Day 1
├── Day 2
├── Day 3
└── Completion

따라서 Task State는 long-term durable state가 되어야 한다.

21. Artifact Relationship

Task State는 Artifact 자체를 포함하지 않고 Reference를 가진다.

Task State
├── Artifact A
├── Artifact B
└── Artifact C

Artifact의 실제 저장과 lifecycle은 Artifact Architecture가 담당한다.

22. Memory Relationship

Memory는 Task State를 대신하지 않는다.

Task State
→ Current progress

Memory
→ Past experience / useful history

둘의 의미를 유지한다.

23. Evaluation Relationship

Evaluation 결과는 Task State를 변경할 수 있다.

예:

Verification Failed
 ↓
Task State
→ Blocked

따라서 Evaluation은 Task State mutation을 유발할 수 있지만
Task State 자체를 소유하지는 않는다.

24. Orchestration Relationship

Orchestrator는 Task State를 읽고:

계획
분해
위임
재계획
Budget allocation

을 수행한다.

하지만 Task State의 canonical persistence를 Orchestrator 내부 Memory로 대체하지 않는다.

25. Security Relationship

Task State 변경도 Policy 대상이 될 수 있다.

State Mutation
 ↓
Policy
 ↓
Permission
 ↓
Commit

특히 중요 상태 변경에는 추가 검증을 요구할 수 있다.

26. Identity Relationship

Task는 Identity보다 하위 개념이다.

Identity
 ↓
Agent
 ↓
Task

Task 실패나 변경이 Identity Core를 자동으로 변경하지 않는다.

27. Responsibility Matrix
Component	Responsibility
Task	Long-term goal
Session	Execution relationship
Task State	Canonical task progress
Runtime	Execution lifecycle
Execution State	Runtime-specific state
Context	Model-facing projection
Orchestrator	Planning / delegation
Memory	Experience / historical information
Artifact	Persistent work product
Evaluation	Quality assessment
28. Consequences
Positive
Long-running Task 지원
Runtime 교체 가능
Pause / Resume 가능
Recovery 가능
Context reconstruction 가능
Session 독립성 증가
Architecture 명확성 증가
Negative
State model이 복잡해짐
Task Store 필요 가능성
Consistency 문제
Side effect tracking 필요
추가 persistence overhead
29. Alternatives Considered
Alternative A — Runtime owns Task State
Task
 ↓
Runtime
 └── State

Rejected.

이유:

Runtime failure에 Task state가 종속
Runtime replacement 어려움
Long-running task 관리 어려움
Alternative B — Session owns Task
Session
 └── Task

Rejected as default.

이유:

Task가 Session보다 오래 지속될 수 있음
Session lifecycle과 Task lifecycle이 강하게 결합
Alternative C — Memory owns Task State

Rejected.

이유:

Memory ≠ Canonical Task State

Memory는 경험과 장기 정보 관리 책임을 가진다.

Alternative D — Event Sourcing as Canonical Source

Deferred.

필요성은 존재하지만 초기에는 과도한 복잡도가 예상된다.

30. Relationship to Other Architecture Decisions

이 Decision은 다음 DDR과 연결된다.

DDR-002
Harness Boundary

DDR-003
Memory / Knowledge Boundary

DDR-004
Artifact Architecture

DDR-005
Identity Persistence

DDR-006
Orchestration Contract

특히:

Task State
↔ Harness
↔ Runtime
↔ Orchestration

관계가 중요하다.

31. Implementation Implications

향후 구현에서는 최소한:

Task
TaskStore
Session
Runtime
ExecutionState
Context
Checkpoint

등의 명확한 경계를 고려한다.

단, 구체적인 Package / Service 구조는 구현 단계에서 결정한다.

32. Validation Plan

이 Decision은 PoC에서 검증한다.

최소 시나리오:

1. Task 생성
2. Runtime 실행
3. Progress 저장
4. Checkpoint
5. Runtime 종료
6. 새로운 Runtime 시작
7. Task State 복원
8. Context 재구성
9. 작업 재개
10. Verification
11. Completion
33. Acceptance Criteria
☐ Runtime 종료 후 Task가 유지된다.
☐ 새로운 Runtime에서 Task를 재개할 수 있다.
☐ Task State와 Execution State가 구분된다.
☐ Context를 재구성할 수 있다.
☐ Artifact Reference가 유지된다.
☐ Verification 결과가 유지된다.
☐ Runtime replacement가 가능하다.
☐ 중복 Side Effect 위험이 추적된다.
34. Decision Status
Status: Accepted
Confidence: Medium

이 Decision은 PoC 결과에 따라 수정될 수 있다.

35. Decision Review Condition

다음 상황에서 이 DDR을 재검토한다.

Long-running Task 요구사항 변화
Runtime Framework 변경
Distributed execution 도입
Event Sourcing 필요성 확인
새로운 Durable Execution 모델 등장
PoC에서 State consistency 문제가 발견됨
36. Final Decision

Project NOAH는 Task State와 Runtime을 분리한다.

Task State는 장기적인 Task의 canonical progress를 유지하며,
Runtime은 실제 Execution Lifecycle을 담당한다.

Runtime은 교체·종료될 수 있지만 Task와 Task State는 지속되어야 한다.

Context는 Task State에서 재구성 가능한 Model-facing projection으로 취급한다.

이 경계는 Long-horizon Task, Pause / Resume, Recovery 및 Runtime replacement를 위한 핵심 Architecture Contract로 사용한다.